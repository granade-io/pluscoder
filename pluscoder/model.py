from langchain_community.chat_models import ChatLiteLLM
from langchain_openai import ChatOpenAI
from langchain_aws import ChatBedrock
from langchain_anthropic import ChatAnthropic
from langchain_community.cache import SQLiteCache
from langchain.globals import set_llm_cache
from pluscoder.io_utils import io
from pluscoder.config import config

# Set up caching to reduce cost/time when calling LLM
# TODO: Fix. Seems not to work along streaming feature
set_llm_cache(SQLiteCache(database_path=".langchain.db"))

# TODO: Fix. Llm Invokes works properly but tools are ignored
def get_llm():
    model_id = config.model
    
    # Raise if no model found
    if model_id is None:
        raise ValueError("No 'model' specified. Please set the 'model' environment variable, .env, or use --model argument.")
    
    # Uses aws bedrock if available
    if config.aws_access_key_id and (not config.provider or config.provider == "aws_bedrock"):
        io.event(f"> Using model '{model_id}' with AWS Bedrock")
        return ChatBedrock(    
            model_id=model_id,
            model_kwargs={"temperature": 0.0, "max_tokens": 4096},
            streaming=config.streaming,
            credentials_profile_name=config.aws_profile
        )
        
    # Uses aws bedrock if available
    if config.anthropic_api_key and (not config.provider or config.provider == "anthropic"):
        io.event(f"> Using model '{model_id}' with Anthropic")
        return ChatAnthropic(    
            model_name=model_id,
            temperature=0.0,
            max_tokens= 4096,
            streaming=config.streaming
        )
        
    # Prefer using OpenAI if available
    if config.openai_api_key and (not config.provider or config.provider == "openai"):
        io.event(f"> Using model '{model_id}' with OpenAI")
        return ChatOpenAI(
            model=model_id.replace("openai/", ""),
            cache=SQLiteCache(database_path=".langchain.db"),
            base_url=config.openai_api_base,
            api_key=config.openai_api_key
        )
    
    # Return ChatLiteLLM
    io.event(f"> Using model '{model_id}' with ChatLiteLLM")
    return ChatLiteLLM(model=model_id)

# Commented out Bedrock LLM configuration
# def get_llm():
#     model_id = os.getenv('model', None)
    
#     # Raise if no model found
#     if model_id is None:
#         raise ValueError("No 'model' specified. Please set the 'model' environment variable or .env.")
    
#     return ChatBedrock(    
#         model_id=model_id,
#         model_kwargs={"temperature": 0.0, "max_tokens": 4096},
#         streaming=True,
#     )