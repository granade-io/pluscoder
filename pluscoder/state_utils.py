from pluscoder.type import AgentState, OrchestrationState, TokenUsage
from litellm import model_cost
from pluscoder.io_utils import io
from pluscoder.config import config


def get_model_token_info(model_name: str) -> dict:
    if model_name in model_cost:
        return model_cost[model_name]
    elif model_name.split("/")[-1] in model_cost:
        return model_cost[model_name.split("/")[-1]]
    return None


def print_token_usage(token_usage: TokenUsage):
    io.console.print(
        f"Tokens: ↑:{token_usage['prompt_tokens']} ↓:{token_usage['completion_tokens']} T:{token_usage['total_tokens']} ${token_usage['total_cost']:.3f}",
        style="yellow",
    )


def sum_token_usage(accumulated: TokenUsage, new: TokenUsage) -> TokenUsage:
    model_info = get_model_token_info(config.model)
    if not model_info:
        # Accumulates normally using cost returned by llm what can be 0 most of the time due small charges
        return {
            "total_tokens": accumulated["total_tokens"] + new["total_tokens"],
            "prompt_tokens": accumulated["prompt_tokens"] + new["prompt_tokens"],
            "completion_tokens": accumulated["completion_tokens"]
            + new["completion_tokens"],
            "total_cost": accumulated["total_cost"] + new["total_cost"],
        }

    # Calculate cost using cost per token data
    input_cost_per_token = model_info.get("input_cost_per_token", 0)
    output_cost_per_token = model_info.get("output_cost_per_token", 0)

    prompt_tokens = accumulated["prompt_tokens"] + new["prompt_tokens"]
    completion_tokens = accumulated["completion_tokens"] + new["completion_tokens"]
    return {
        "total_tokens": accumulated["total_tokens"] + new["total_tokens"],
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_cost": (
            prompt_tokens * input_cost_per_token
            + completion_tokens * output_cost_per_token
        ),
    }


def accumulate_token_usage(
    global_state: OrchestrationState, _state: AgentState
) -> OrchestrationState:
    if "token_usage" not in _state:
        return global_state

    # Update token usage
    accumulated_token_usage = sum_token_usage(
        global_state.get(
            "accumulated_token_usage",
            {
                "total_tokens": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_cost": 0.0,
            },
        ),
        _state["token_usage"],
    )
    global_state["accumulated_token_usage"] = accumulated_token_usage

    # TODO: track accumulated token usage for every agent
    print_token_usage(accumulated_token_usage)

    return global_state
