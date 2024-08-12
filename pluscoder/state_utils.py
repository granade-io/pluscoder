from pluscoder.type import AgentState, OrchestrationState, TokenUsage
from pluscoder.io_utils import io


def print_token_usage(token_usage: TokenUsage):
    io.console.print(f"Tokens: ↑:{token_usage['prompt_tokens']} ↓:{token_usage['completion_tokens']} T:{token_usage['total_tokens']} ${token_usage['total_cost']:.8f}")
    
def sum_token_usage(accumulated: TokenUsage, new: TokenUsage) -> TokenUsage:
    return {
        "total_tokens": accumulated["total_tokens"] + new["total_tokens"],
        "prompt_tokens": accumulated["prompt_tokens"] + new["prompt_tokens"],
        "completion_tokens": accumulated["completion_tokens"] + new["completion_tokens"],
        "total_cost": accumulated["total_cost"] + new["total_cost"]
    }

def accumulate_token_usage(global_state: OrchestrationState, _state: AgentState) -> OrchestrationState:
        if not "token_usage" in _state:
            return global_state
        
        # Update token usage
        accumulated_token_usage = sum_token_usage(
            global_state.get("accumulated_token_usage", {"total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_cost": 0.0}),
            _state["token_usage"]
        )
        global_state["accumulated_token_usage"] = accumulated_token_usage
        
        # TODO: track accumulated token usage for every agent
        print_token_usage(accumulated_token_usage)
        
        return global_state