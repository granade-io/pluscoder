import functools
import warnings

from langchain_core.globals import set_debug
from langchain_core.messages import AIMessage
from langgraph.graph import END
from langgraph.graph import START
from langgraph.graph import StateGraph
from rich.markdown import Markdown
from rich.rule import Rule

from pluscoder import tools
from pluscoder.agents.base import Agent
from pluscoder.agents.core import DeveloperAgent
from pluscoder.agents.core import DomainExpertAgent
from pluscoder.agents.core import DomainStakeholderAgent
from pluscoder.agents.core import PlanningAgent
from pluscoder.agents.custom import CustomAgent
from pluscoder.agents.event.config import event_emitter
from pluscoder.agents.orchestrator import OrchestratorAgent
from pluscoder.commands import handle_command
from pluscoder.commands import is_command
from pluscoder.config import config
from pluscoder.io_utils import io
from pluscoder.message_utils import HumanMessage
from pluscoder.message_utils import delete_messages
from pluscoder.message_utils import filter_messages
from pluscoder.message_utils import get_message_content_str
from pluscoder.state_utils import accumulate_token_usage
from pluscoder.type import OrchestrationState

set_debug(False)

# Ignore deprecation warnings
warnings.filterwarnings("ignore")


def build_agents() -> dict:
    # Create the vision agent
    orchestrator_agent = OrchestratorAgent()
    domain_stakeholder_agent = DomainStakeholderAgent()
    planning_agent = PlanningAgent()
    developer_agent = DeveloperAgent()
    domain_expert_agent = DomainExpertAgent()

    # Initialize custom agents
    custom_agents = []
    for agent_config in config.custom_agents:
        custom_agent = CustomAgent(
            name=agent_config["name"],
            prompt=agent_config["prompt"],
            description=agent_config["description"],
            reminder=agent_config.get("reminder", ""),
            read_only=agent_config.get("read_only", False),
            override_system=agent_config.get("override_system", False),
            repository_interaction=agent_config.get("repository_interaction", True),
        )
        custom_agents.append(custom_agent)

    # Update the available_agents list to include custom agents
    available_agents = [
        orchestrator_agent,
        domain_stakeholder_agent,
        planning_agent,
        developer_agent,
        domain_expert_agent,
    ] + custom_agents

    # Create a dictionary mapping agent names to their instances
    return {agent.id: agent for agent in available_agents}


def user_input(state: OrchestrationState):
    if state["is_task_list_workflow"]:
        # Handle task list workflow. Do not append any user message
        return {"return_to_user": False}

    if config.user_input:
        user_input = config.user_input
    else:
        io.console.print()
        io.console.print(
            "[bold green]Enter your message ('q' or 'ctrl+c' to exit, '/help' for commands): [/bold green]"
        )
        user_input = io.input("")

    if is_command(user_input):
        # Commands handles the update to state
        # updated_state
        return handle_command(user_input, state=state)

    # Routes messages to the chosen agent

    return {
        "return_to_user": False,
        "messages": HumanMessage(content=user_input, tags=[state["chat_agent"]]),
        "current_iterations": state["current_iterations"] + 1,
    }


def user_router(state: OrchestrationState):
    """Decides where to go after the user input in orchestrate mode."""
    # Almost all commands redirect to the user by default
    if state["return_to_user"]:
        return "user_input"

    if state["is_task_list_workflow"]:
        # If running a task list workflow, go to the agent
        return state["chat_agent"]

    user_message = state["messages"][-1].content
    user_input = user_message.strip().lower() if type(user_message) is str else user_message

    # On empty user inputs return to the user
    if not user_input:
        return "user_input"

    if user_input == "q":
        return END

    return state["chat_agent"]  # Go to chat agent


def orchestrator_router(state: OrchestrationState, orchestrator_agent: OrchestratorAgent) -> str:
    """Decides the next step in orchestrate mode."""

    if (
        state["status"] == "active"
        and (orchestrator_agent.is_task_list_empty(state) or orchestrator_agent.is_task_list_complete(state))
        and state["current_iterations"] >= state["max_iterations"]
    ):
        return END

    # Returns to the user when user requested by confirmation input
    if state["return_to_user"]:
        return "user_input"

    task = orchestrator_agent.get_current_task(state)

    # When summarizing result into a response or when there are no more tasks, end the interaction if user_input is defined or is a task list workflow
    if state["status"] == "summarizing" or task is None:
        return END if config.user_input or state["is_task_list_workflow"] else "user_input"

    # When delegating always delegate to other agents
    if state["status"] == "delegating":
        return task["agent"]

    # When active and a task is available, orchestrator runs again to add instruction to the executor agent's state
    return orchestrator_agent.id


def agent_router(state: OrchestrationState, orchestrator_agent: OrchestratorAgent) -> str:
    """Decides where to go after an agent was called."""
    if state["current_iterations"] >= state["max_iterations"] and (state["chat_agent"] != orchestrator_agent.id):
        return END

    if state["chat_agent"] == orchestrator_agent.id:
        # Always return to the orchestrator when called by the orchestrator
        return orchestrator_agent.id

    if config.user_input:
        # if called from bash input, exits graph
        return END

    # Otherwise return to the user
    return "user_input"


async def _agent_node(state: OrchestrationState, agent: Agent) -> OrchestrationState:
    """
    Agent node process its message list to return a new answer and a updated state
    """

    # Returns to the user when user requested by confirmation input
    if state["return_to_user"]:
        return state

    # Display agent information
    io.console.print(Rule(agent.name))

    # Execute the agent's graph node and get a its modified state
    messages = filter_messages(state["messages"], include_tags=[agent.id])
    updated_state = await agent.graph_node({**state, "messages": messages})
    # Update token usage
    # state = accumulate_token_usage(state, updated_state)

    # orchestrated agent doesn't need to update its state, is was already updated by the internal graph execution
    return {"messages": updated_state["messages"], "accumulated_token_usage": state["accumulated_token_usage"]}


async def _orchestrator_agent_node(
    state: OrchestrationState, orchestrator_agent: OrchestratorAgent
) -> OrchestrationState:
    """
    Agent node process its message list to return a new answer and a updated state
    Orchestrator acts as an user when talking to other agents.
    Orchestrator can to 4 things:
    1. Define a list on tasks for agents and put them in the state under tools_data
    2. Check current task list to delegate tasks to other agents.
    3. Validate if the received agent message completed or not the current task.
    4. Respond to the caller when no tasks are left. Usually responds to the user.
    """

    # Helper to update the global state
    global_state = state

    # Active behaviour when orchestrator receives a message
    if global_state["status"] == "active":
        # If user message and no active task (or are all completed)
        if not orchestrator_agent.is_agent_response(global_state) and not global_state["is_task_list_workflow"]:
            # Display agent information
            io.console.print(Rule(orchestrator_agent.id))

            # User message received
            messages = filter_messages(state["messages"], include_tags=[orchestrator_agent.id])
            return await orchestrator_agent.graph_node({**state, "messages": messages})

        # Active tasks to delegate to other agents
        # Assume all agent messages are from orchestrator itself

        # Get current task. Task can also exist during active mode if were injected to the state from another process
        task = orchestrator_agent.get_current_task(global_state)
        if task:
            # Log task list
            io.log_to_debug_file(json_data=orchestrator_agent.get_task_list(global_state))

            # Print task list as Markdown
            agent_instructions = orchestrator_agent.get_agent_instructions(global_state)
            markdown_content = agent_instructions.to_markdown()
            io.console.print(Markdown(markdown_content))

            # Ask the user for confirmation to proceed
            if not io.confirm("Do you want to proceed?"):
                state = orchestrator_agent.remove_task_list_data(global_state)
                return {
                    **state,
                    "return_to_user": True,
                }

            # Task was found means the tool was successful called while in active mode and we need to delegate it to other agents
            await event_emitter.emit(
                "new_agent_instructions",
                agent_instructions=orchestrator_agent.get_agent_instructions(global_state),
            )
            target_agent = task["agent"]

            # Delegate the task to the target agent
            return {
                "status": "delegating",
                "messages": HumanMessage(
                    content=orchestrator_agent.task_to_instruction(task, state), tags=[target_agent]
                ),
            }

        # We assume other tool was called and respond to the caller
        # TODO check what meas respond to the caller
        return {"messages": []}

    # Delegating mode

    # We assume received messages are from the agent executing the task
    # internal behavior changes automatically due state.status value

    task = orchestrator_agent.get_current_task(global_state)
    task_objective, task_details = task["objective"], task["details"]
    target_agent = task["agent"]

    # Add response message from the executor agent to validate if the task has been completed
    executor_agent_response = get_message_content_str(global_state["messages"][-1])

    # Validates using only last message not entire conversation
    await event_emitter.emit(
        "task_validation_start",
        agent_instructions=orchestrator_agent.get_agent_instructions(global_state),
    )
    validation_response = await orchestrator_agent.graph_node(
        {
            **global_state,
            "messages": [
                HumanMessage(
                    content=f"Validate if the current task was completed by the agent:\nTask objective: {task_objective}\nTask Details:{task_details}\n\nAgent response:\n{executor_agent_response}",
                    tags=[orchestrator_agent.id + "-" + target_agent],
                )
            ],
        }
    )

    # Update global tokens
    global_state = accumulate_token_usage(global_state, validation_response)

    if not orchestrator_agent.was_task_validation_tool_used(validation_response):
        # Task ALWAYS must be used when validating the current task
        raise ValueError("Validation tool did not return a boolean value")
    if orchestrator_agent.validate_current_task_completed(validation_response) or (
        # Manual validation when max reflections are reached
        global_state["current_agent_deflections"] >= global_state["max_agent_deflections"]
        and io.confirm(f"Was the task `{task["objective"]}` completed by the agent?")
    ):
        # Task has been completed. Move to next task

        state_update = orchestrator_agent.mark_current_task_as_completed(global_state, executor_agent_response)
        await event_emitter.emit(
            "task_completed",
            agent_instructions=orchestrator_agent.get_agent_instructions(state_update),
        )

        # Check if there are more tasks to delegate
        if orchestrator_agent.is_task_list_complete(state_update):
            await event_emitter.emit(
                "task_list_completed",
                agent_instructions=orchestrator_agent.get_agent_instructions(state_update),
            )

            # Display agent information
            io.console.print(Rule(orchestrator_agent.id))

            # Generate a final summarized answer to the user
            task_results = "\n---\n".join(
                [
                    f"Task: {task["objective"]}\nDetails: {task["details"]}\nResponse: {task["response"]}"
                    for task in orchestrator_agent.get_task_list(state_update)
                ]
            )
            final_response = await orchestrator_agent.graph_node(
                {
                    **state_update,
                    "status": "summarizing",  # Next call to the orchestrator is to summarize the results
                    "messages": [
                        HumanMessage(
                            content=f"Based on the following responses of other agents to my last requirement; generate a final summarized answer for me:\n{task_results}",
                            tags=[orchestrator_agent.id + "-" + orchestrator_agent.id],
                        )
                    ],
                }
            )

            state_update = accumulate_token_usage(state_update, final_response)

            # cleaned tool data
            tool_data = {**state_update["tool_data"]}
            tool_data.pop(tools.delegate_tasks.name, None)

            # no more tasks to delegate. Return to user by setting status to active. Resets the agent messages
            return {
                **state_update,
                "tool_data": tool_data,
                "messages": [
                    *delete_messages(
                        state_update["messages"],
                        include_tags=[target_agent, orchestrator_agent.id + "-" + orchestrator_agent.id],
                    ),
                    *filter_messages(final_response["messages"], include_tags=[orchestrator_agent.id]),
                ],
                "status": "active",
            }

        io.event("> [bold]Task completed![/bold]")

        # Ask the user for confirmation to proceed
        if not io.confirm("Do you want to proceed with next task?"):
            await event_emitter.emit(
                "task_list_interrumpted",
                agent_instructions=orchestrator_agent.get_agent_instructions(state_update),
            )

            # cleaned tool data
            tool_data = {**global_state["tool_data"]}
            tool_data.pop(tools.delegate_tasks.name, None)

            # Return to user to give obtain more feedback & set status to active to allow agent to
            # execute its default behavior
            return {
                **state_update,
                "status": "active",
                "return_to_user": True,
                "messages": [
                    *delete_messages(
                        state_update["messages"],
                        include_tags=[target_agent, orchestrator_agent.id + "-" + orchestrator_agent.id],
                    ),
                    AIMessage(
                        content=f"Some tasks of the list were completed, not sure if successfully. Here is the full task list:\n\n{orchestrator_agent.get_agent_instructions(state_update)!s}",
                        tags=[orchestrator_agent.id],
                    ),
                ],
                "tool_data": tool_data,
            }
        io.event("> [bold]Moving to next task... [/bold]")

        task = orchestrator_agent.get_current_task(state_update)
        # Delegating the task to the next agent
        await event_emitter.emit(
            "task_delegated",
            agent_instructions=orchestrator_agent.get_agent_instructions(state_update),
        )
        global_updated = accumulate_token_usage(global_state, state_update)

        # Next target agent
        next_target_agent = task["agent"]
        return {
            **global_updated,
            # Adds message to new agent
            "messages": [
                *delete_messages(global_updated["messages"], include_tags=[target_agent]),
                HumanMessage(content=orchestrator_agent.task_to_instruction(task, state), tags=[next_target_agent]),
            ],
            # Resets global state agent deflections
            "current_agent_deflections": 0,
        }

    # Task is still incomplete. Keep delegating to the same agent

    if global_state["current_agent_deflections"] >= global_state["max_agent_deflections"]:
        # Max reflections reached and user does not confirm the task as completed.
        io.event("> Max reflections reached. Validate changes and refine task list properly.")

        await event_emitter.emit(
            "task_list_interrumpted",
            agent_instructions=orchestrator_agent.get_agent_instructions(state_update),
        )

        return {
            "status": "active",
            "return_to_user": True,
        }

    await event_emitter.emit(
        "task_delegated",
        agent_instructions=orchestrator_agent.get_agent_instructions(global_state),
    )
    return {
        "messages": [
            HumanMessage(content=orchestrator_agent.task_to_instruction(task, state), tags=[target_agent]),
        ],
        "current_agent_deflections": global_state["current_agent_deflections"] + 1,
    }


def build_workflow(agents: dict):
    # Instance agents
    orchestrator_agent = agents[OrchestratorAgent.id]

    # Crating orchestrator agent
    orchestrator_agent_node = functools.partial(_orchestrator_agent_node, orchestrator_agent=orchestrator_agent)
    # Create vision + custom agent nodes
    agent_nodes = {}
    for agent_id, agent in agents.items():
        if agent_id == orchestrator_agent.id:
            continue
        agent_nodes[agent_id] = functools.partial(_agent_node, agent=agent)

    # Routers
    orchestrator_router_node = functools.partial(orchestrator_router, orchestrator_agent=orchestrator_agent)
    agent_router_node = functools.partial(agent_router, orchestrator_agent=orchestrator_agent)

    # Create the graph
    workflow = StateGraph(OrchestrationState)

    # Add nodes
    workflow.add_node("user_input", user_input)
    workflow.add_node(orchestrator_agent.id, orchestrator_agent_node)
    # workflow.add_node("state_preparation", orchestrator_agent.state_preparation_node)

    # Add custom agent nodes
    for agent_id, agent_node in agent_nodes.items():
        workflow.add_node(agent_id, agent_node)

    # Add edges
    workflow.add_edge(START, "user_input")
    workflow.add_conditional_edges("user_input", user_router)
    workflow.add_conditional_edges(orchestrator_agent.id, orchestrator_router_node)

    # Add edges for custom agents
    for agent_id in agent_nodes:
        workflow.add_conditional_edges(agent_id, agent_router_node)

    # Set the entrypoint
    # workflow.set_entry_point("user_input")

    # Compile the workflow
    return workflow.compile()


# Run the workflow
async def run_workflow(app, state: OrchestrationState) -> None:
    return await app.ainvoke(state, config={"recursion_limit": 100})
