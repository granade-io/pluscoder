from langchain_community.chat_models import ChatLiteLLM
from langchain_openai import ChatOpenAI
from langchain_aws import ChatBedrock
from langchain_anthropic import ChatAnthropic
from pluscoder.io_utils import io
from pluscoder.config import config


def get_llm_base(model_id, provider):
    # Check AWS Bedrock
    if provider == "aws_bedrock" and not config.aws_access_key_id:
        io.console.print(
            "AWS Bedrock provider defined but AWS access key ID is not configured or empty.",
            style="bold red",
        )

    # Check Anthropic
    if provider == "anthropic" and not config.anthropic_api_key:
        io.console.print(
            "Anthropic provider defined but Anthropic API key is not configured or empty.",
            style="bold red",
        )

    # Check OpenAI
    if provider == "openai" and not config.openai_api_key:
        io.console.print(
            "OpenAI provider defined but OpenAI API key is not configured or empty.",
            style="bold red",
        )

    # Uses aws bedrock if available
    if config.aws_access_key_id and provider == "aws_bedrock":
        return ChatBedrock(
            model_id=model_id,
            model_kwargs={"temperature": 0.0, "max_tokens": 4096},
            streaming=config.streaming,
            credentials_profile_name=config.aws_profile,
        )

    # Uses Anthropic if available
    if config.anthropic_api_key and provider == "anthropic":
        return ChatAnthropic(
            model_name=model_id,
            temperature=0.0,
            max_tokens=4096,
            streaming=config.streaming,
        )

    # Uses OpenAI if available
    if config.openai_api_key and provider == "openai":
        return ChatOpenAI(
            model=model_id.replace("openai/", ""),
            base_url=config.openai_api_base,
            api_key=config.openai_api_key,
            max_tokens=4096,
        )

    # Uses Litellm
    if config.openai_api_key and provider == "litellm":
        return ChatLiteLLM(model=model_id)

    # Return no model
    return None


def get_llm():
    return get_llm_base(config.model, config.provider or get_inferred_provider())


def get_orchestrator_llm():
    model = config.orchestrator_model if config.orchestrator_model else config.model
    provider = (
        config.orchestrator_model_provider or config.provider or get_inferred_provider()
    )
    return get_llm_base(model, provider)


def get_weak_llm():
    model = config.weak_model if config.weak_model else config.model
    provider = config.weak_model_provider or config.provider or get_inferred_provider()
    return get_llm_base(model, provider)


def get_inferred_provider():
    if config.provider:
        return config.provider

    # Uses aws bedrock if available
    if config.aws_access_key_id:
        return "aws_bedrock"

    # Uses Anthropic if available
    if config.anthropic_api_key:
        return "anthropic"

    # Prefer using OpenAI if available
    if config.openai_api_key:
        return "openai"

    return "litellm"


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
