import functools
import warnings

from pluscoder.agents.orchestrator import OrchestratorAgent
from pluscoder.io_utils import io
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import HumanMessage
from pluscoder.agents.base import Agent, AgentState
from pluscoder.state_utils import accumulate_token_usage
from pluscoder.type import OrchestrationState, TokenUsage
from pluscoder.agents.core import DeveloperAgent, DomainStakeholderAgent, PlanningAgent, DomainExpertAgent
from rich.rule import Rule
from rich.markdown import Markdown
from langchain_core.globals import set_debug
from pluscoder.message_utils import get_message_content_str
from pluscoder.model import get_llm
from pluscoder.agents.event.config import event_emitter
from pluscoder.commands import handle_command, is_command
from pluscoder.config import config

set_debug(False)

# Ignore deprecation warnings
warnings.filterwarnings("ignore")

llm = get_llm()

# Create the vision agent
orchestrator_agent = OrchestratorAgent(llm)
domain_stakeholder_agent = DomainStakeholderAgent(llm)
planning_agent = PlanningAgent(llm)
developer_agent = DeveloperAgent(llm)
domain_expert_agent = DomainExpertAgent(llm)

# Orchestrator now handles agent selection, so we don't need to set a default agent

# OrchestrationState is now imported from pluscoder.type
    
def get_chat_agent_state(state: OrchestrationState) -> AgentState:
    return state[state.chat_agent + "_state"]

def user_input(state: OrchestrationState):
    
    if state["is_task_list_workflow"]:
        # Handle task list workflow. Do not append any user message
        return {"return_to_user": False}
    
    if config.user_input:
        user_input = config.user_input
    else:
        io.console.print()
        io.console.print("[bold green]Enter your message ('q' to exit, '/help' for commands): [/bold green]")
        user_input = io.input('')
    
    if is_command(user_input):
        # Commands handles the update to state
        updated_state = handle_command(user_input, state=state)
        return updated_state
    
    # Routes messages to the chosen agent
    chat_agent_id = state["chat_agent"] + "_state"
    chat_agent_state = state[chat_agent_id]
    
    return {"return_to_user": False,
            chat_agent_id: {**chat_agent_state, "messages": chat_agent_state["messages"] + [HumanMessage(content=user_input)]}
            }

def user_router(state: OrchestrationState):
    """Decides where to go after the user input in orchestrate mode."""
    # Almost all commands redirect to the user by default
    if state["return_to_user"]:
        return "user_input"
    
    if state["is_task_list_workflow"]:
        # If running a task list workflow, go to the agent
        return state["chat_agent"]
    
    user_input = state[state["chat_agent"] + "_state"]["messages"][-1].content.strip().lower()
    
    # On empty user inputs return to the user
    if not user_input:
        return "user_input"

    if user_input == "q":
        return END
    
    return state["chat_agent"]  # Go to chat agent

def router(state: OrchestrationState):
    """Decides the next step in orchestrate mode."""
    
    # Returns to the user when user requested by confirmation input
    if state["return_to_user"]:
        return "user_input"
    
    orch_state = state[orchestrator_agent.id + "_state"]
    
    task = orchestrator_agent.get_current_task(orch_state)
    
    # When summarizing result into a response or when there are no more tasks, end the interaction if user_input is defined or is a task list workflow
    if orch_state["status"] == "summarizing" or task is None:
        return END if config.user_input or state["is_task_list_workflow"] else "user_input"
    
    # When delegating always delegate to other agents
    if orch_state["status"] == "delegating":
        return task["agent"]
    
    # When active and a task is available, orchestrator runs again to add instruction to the executor agent's state
    return orchestrator_agent.id

def agent_router(state: OrchestrationState) -> str:
    """Decides where to go after an agent was called."""
    
    if state["chat_agent"] != orchestrator_agent.id:
        # When chatting an agent different from the orchestrator, go back to the user
        return "user_input"
    
    # Return to the orchestrator
    return orchestrator_agent.id

async def agent_node(state: OrchestrationState, agent: Agent) -> OrchestrationState:
    """
    Agent node process its message list to return a new answer and a updated state
    """
    
    # Returns to the user when user requested by confirmation input
    if state["return_to_user"]:
        return state
    
    # Get the current state of the agent
    agent_state = state[agent.id + "_state"] 
    
    # Display agent information
    io.console.print(Rule(agent.id))
    
    # Execute the agent's graph node and get a its modified state
    agent_state_output = await agent.graph_node(agent_state)
    
    # Update token usage
    state = accumulate_token_usage(state, agent_state_output)
    
    # orchestrated agent doesn't need to update its state, is was already updated by the internal graph execution
    return {**state, agent.id + "_state": {**agent_state, **agent_state_output}}

async def orchestrator_agent_node(state: OrchestrationState, agent: OrchestratorAgent) -> OrchestrationState:
    """
    Agent node process its message list to return a new answer and a updated state
    Orchestrator acts as an user when talking to other agents.
    Orchestrator can to 4 things:
    1. Define a list on tasks for agents and put them in the state under tools_data
    2. Check current task list to delegate tasks to other agents.
    3. Validate if the received agent message completed or not the current task.
    4. Responde to the caller when no tasks are left. Usually responds to the user.
    """
    
    # Helper to update the global state
    global_state = state

    def update_global_state(_agent_id, _updated_state):
        _global_state = accumulate_token_usage(global_state, _updated_state)
        _current_state = _global_state[_agent_id + "_state"]
        
        # Token usage becomes none to avoid counting twice
        _global_state[_agent_id + "_state"] = {**_current_state, **_updated_state, "token_usage": TokenUsage.default()}
        
        return _global_state
    
    # Get the current state of the agent
    state = state[agent.id + "_state"] 
    
    # Active behaviour when orchestrator receives a message
    if state["status"] == "active":
        
        # If user message and no active task (or are all completed)
        if not orchestrator_agent.is_agent_response(state) and not global_state["is_task_list_workflow"]:
            
            # Display agent information
            io.console.print(Rule(agent.id))
            
            # User message received
            state_output = await agent.graph_node(state)
            
            # Messages already appended to the state by previous call
            return update_global_state(agent.id, state_output)
        
        # Active tasks to delegate to other agents
        # Assume all agent messages are from orchestrator itself
        
        # Get current task. Task can also exist during active mode if were inyected to the state from another process
        task = orchestrator_agent.get_current_task(state)
        if task:
            # Log task list
            io.log_to_debug_file(json_data=orchestrator_agent.get_task_list(state))
            
            # Print task list as Markdown
            agent_instructions = orchestrator_agent.get_agent_instructions(state)
            markdown_content = agent_instructions.to_markdown()
            io.console.print(Markdown(markdown_content))
            
            # Ask the user for confirmation to proceed
            if not io.confirm("Do you want to proceed?"):
                state = orchestrator_agent.remove_task_list_data(state)
                return {
                    **update_global_state(agent.id, state),
                    "return_to_user": True,
                }
            
            # Task was found means the tool was successful called while in active mode and we need to delegate it to other agents
            await event_emitter.emit("new_agent_instructions", agent_instructions=orchestrator_agent.get_agent_instructions(state))
            target_agent = task["agent"]
            
            # Gets the state of the target agent
            target_agent_state = global_state[target_agent + "_state"]
            
            # Delegate the task to the target agent
            return {**update_global_state(agent.id, {"status": "delegating"}), 
                    **update_global_state(target_agent, {"messages": target_agent_state["messages"] + [HumanMessage(content=orchestrator_agent.task_to_instruction(task, state))]})}
        
        # We asume other tool was called and respond to the caller
        # TODO check what meas respond to the caller
        return update_global_state(agent.id, {"messages": []})
    
    # Delegating mode
        
    # We asume received messages are from the agent executing the task
    # internal behavior changes automatically due state.status value
    
    task = orchestrator_agent.get_current_task(state)
    task_objective, task_details = task["objective"], task["details"]
    target_agent = task["agent"]
    # Gets the state of the target agent
    target_agent_state = global_state[target_agent + "_state"]
    
    # Add response message from the executor agent to validate if the task has been completed
    executor_agent_response = get_message_content_str(target_agent_state["messages"][-1])
    # state = {**state, "agent_messages": state["agent_messages"] + }
    
    # io.event(f"> [bold]Agent response received. Checking if task has been completed")
    
    # Validates using only last message not entire conversation
    await event_emitter.emit("task_validation_start", agent_instructions=orchestrator_agent.get_agent_instructions(state))
    validation_response = await agent.graph_node({**state, "messages": [HumanMessage(content=f"Validate if the current task was completed by the agent:\nTask objective: {task_objective}\nTask Details:{task_details}\n\nAgent response:\n{executor_agent_response}")]})
    
    # Update global tokens
    global_state = accumulate_token_usage(global_state, validation_response)
    
    if not agent.was_task_validation_tool_used(validation_response):
        # Task ALWAYS must be used when validating the current task
        raise ValueError("Validation tool did not return a boolean value")
    elif agent.validate_current_task_completed(validation_response) or (
            # Manual validation when max reflections are reached
            global_state["current_agent_deflections"] >= global_state["max_agent_deflections"] and \
            io.confirm(f"Was the task `{task["objective"]}` completed by the agent?")
            ): 
        # Task has been completed. Move to next task
        
        state_update = agent.mark_current_task_as_completed(state, executor_agent_response)
        await event_emitter.emit("task_completed", agent_instructions=orchestrator_agent.get_agent_instructions(state_update))
        
        # Check if there are more tasks to delegate
        if agent.is_task_list_complete(state_update):
            await event_emitter.emit("task_list_completed", agent_instructions=orchestrator_agent.get_agent_instructions(state_update))
            
            # Display agent information
            io.console.print(Rule(agent.id))
            
            # Generate a final summarized answer to the user 
            task_results = "\n---\n".join([f"Task: {task["objective"]}\nDetails: {task["details"]}\nResponse: {task["response"]}" for task in orchestrator_agent.get_task_list(state)])
            final_response = await agent.graph_node({
                **state_update, 
                "status": "summarizing",  ## Next call to the orchestrator is to summarize the results
                "messages": state_update["messages"] + [HumanMessage(content=f"Based on the following responses of other agents to my last requirement; generate a final summarized answer for me:\n{task_results}")]
                })
            
            # no more tasks to delegate. Return to user by setting status to active. Resets the agent messages
            return update_global_state(agent.id, {**final_response, "status": "active", "agent_messages": []})
        
        io.event("> [bold]Task completed![/bold]")
        
        # Ask the user for confirmation to proceed
        if not io.confirm("Do you want to proceed with next task?"):
            await event_emitter.emit("task_list_interrumpted", agent_instructions=orchestrator_agent.get_agent_instructions(state_update))
            
            # Return to user to give obtain more feedback & set status to active to allow agent to execute its default behavior
            return {
                **update_global_state(agent.id, {**state_update, "status": "active"}),
                "return_to_user": True,
            }
        io.event("> [bold]Moving to next task... [/bold]")
            
        task = agent.get_current_task(state_update)
        # Delegating the task to the next agent
        await event_emitter.emit("task_delegated", agent_instructions=orchestrator_agent.get_agent_instructions(state))
        global_updated = update_global_state(target_agent, state_update)
        
        # Next target agent
        next_target_agent = task["agent"]
        return {
            **global_updated, 
            # Resets target agent state because finished his task
            f"{target_agent}_state": AgentState.default(),
            
            # Adds message to new agent
            f"{next_target_agent}_state": {**AgentState.default(), "messages": [HumanMessage(content=orchestrator_agent.task_to_instruction(task, state))]},
            
            # Update orchestrator with validation response
            f"{agent.id}_state": {**global_updated[f"{agent.id}_state"], "agent_messages": []},
            
            # Resets global state agent deflections
            "current_agent_deflections": 0
        }

    # Task is still incomplete. Keep delegating to the same agent
    # io.event(f"> [bold]Task incompleted. Re-delegating. [/bold]")
    
    if global_state["current_agent_deflections"] >= global_state["max_agent_deflections"]:
        # Max reflections reached and user does not confirm the task as completed.
        io.event("> Max reflections reached. Validate changes and refine task list properly.")
        
        await event_emitter.emit("task_list_interrumpted", agent_instructions=orchestrator_agent.get_agent_instructions(state_update))
        
        return {
            **update_global_state(agent.id, {**state, "status": "active"}),
            "return_to_user": True,
        }
    
    # Get target agent messages
    messages = target_agent_state["messages"]
    await event_emitter.emit("task_delegated", agent_instructions=orchestrator_agent.get_agent_instructions(state))
    global_updated = update_global_state(target_agent, {"messages": messages + [HumanMessage(content=agent.task_to_instruction(task, state))]})
    global_updated = {
        **global_updated, 
        **update_global_state(agent.id, {"agent_messages": validation_response["messages"]}),
        "current_agent_deflections": global_updated["current_agent_deflections"] + 1,
        }
    return global_updated
    

orchestrator_agent_node = functools.partial(orchestrator_agent_node, agent=orchestrator_agent)
domain_stakeholder_agent_node = functools.partial(agent_node, agent=domain_stakeholder_agent)
planning_agent_node = functools.partial(agent_node, agent=planning_agent)
developer_agent_node = functools.partial(agent_node, agent=developer_agent)
domain_expert_agent_node = functools.partial(agent_node, agent=domain_expert_agent)


# Create the graph
workflow = StateGraph(OrchestrationState)

# Add nodes
workflow.add_node("user_input", user_input)
workflow.add_node(orchestrator_agent.id, orchestrator_agent_node)
# workflow.add_node("state_preparation", orchestrator_agent.state_preparation_node)
workflow.add_node("domain_stakeholder", domain_stakeholder_agent_node)
workflow.add_node("planning", planning_agent_node)
workflow.add_node("developer", developer_agent_node)
workflow.add_node("domain_expert", domain_expert_agent_node)

# Add edges
workflow.add_edge(START, "user_input")
workflow.add_conditional_edges("user_input", user_router)
workflow.add_conditional_edges(orchestrator_agent.id, router)
workflow.add_conditional_edges("domain_stakeholder", agent_router)
workflow.add_conditional_edges("planning", agent_router)
workflow.add_conditional_edges("developer", agent_router)
workflow.add_conditional_edges("domain_expert", agent_router)

# Set the entrypoint
# workflow.set_entry_point("user_input")

# Compile the workflow
app = workflow.compile()

# Run the workflow

async def run_workflow(state: OrchestrationState) -> None:
    
    async for event in app.astream_events(state, config={"recursion_limit": 100}, version="v1"):
            kind = event["event"]
            if kind == "on_chain_end":
                pass
