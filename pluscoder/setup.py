from pluscoder.repo import Repository
from pluscoder.io_utils import io
from pluscoder.config import config
from pluscoder.state_utils import get_model_token_info

def setup() -> bool:
    # Check repository setup
    repo = Repository(io=io)
    if not repo.setup():
        io.console.print("Exiting pluscoder", style="bold dark_goldenrod")
        return False
    
    # Warns token cost
    if not get_model_token_info(config.model):
        io.console.print(f"Token usage info not available for model `{config.model}`. Cost calculation can be unaccurate.", style="bold dark_goldenrod")
    return True