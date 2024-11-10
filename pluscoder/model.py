from functools import lru_cache
from typing import Optional

from langchain_anthropic import ChatAnthropic
from langchain_aws import ChatBedrock
from langchain_community.chat_models import ChatLiteLLM
from langchain_openai import ChatOpenAI

from pluscoder.config import config


def _get_model_cost() -> dict:
    if hasattr(_get_model_cost, "model_cost"):
        return _get_model_cost.model_cost

    def get_from_litellm():
        from litellm import model_cost

        return model_cost

    def get_from_json():
        import json
        import pkgutil

        file = pkgutil.get_data("assets", "model_cost.json")
        return json.loads(file)

    def default():
        return {}

    for method in (get_from_litellm, get_from_json, default):
        try:
            model_cost = method()
        except Exception:
            # You might want to log the exception or handle it differently
            continue
        else:
            _get_model_cost.model_cost = model_cost
            return model_cost

    # If all methods fail, raise an exception or return a default value
    msg = "Unable to load model_cost from any source."
    raise RuntimeError(msg)


def _get_provider_model() -> dict:
    if hasattr(_get_provider_model, "default_model"):
        return _get_provider_model.default_model

    def get_from_cost():
        _model_cost = _get_model_cost()
        return {
            data.get("litellm_provider"): model for model, data in _model_cost.items() if data.get("mode") == "chat"
        }

    def get_from_json():
        import json
        import os
        import pkgutil

        file = pkgutil.get_data("assets", "model_default.json")
        if file is not None:
            return json.loads(file)

        assets_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets"))
        file = os.path.join(assets_folder, "model_default.json")
        with open(file, "r") as f:
            return json.load(f)

    def default():
        return {
            "bedrock": "anthropic.claude-3-5-sonnet-20240620-V1:0",
            "openai": "gpt-4o",
            "anthropic": "claude-3-5-sonnet-20240620",
        }

    for method in (get_from_json, get_from_cost, default):
        try:
            default_model = method()
        except Exception:
            # You might want to log the exception or handle it differently
            continue
        else:
            _get_provider_model.default_model = default_model
            return default_model

    # If all methods fail, raise an exception or return a default value
    msg = "Unable to load model_default from any source."
    raise RuntimeError(msg)


@lru_cache
def get_model_token_info(model_name: str) -> dict:
    model_cost = _get_model_cost()
    if model_name in model_cost:
        return model_cost[model_name]
    if model_name.split("/")[-1] in model_cost:
        return model_cost[model_name.split("/")[-1]]
    for key in model_cost:
        if model_name in key:
            return model_cost[key]
    return None


@lru_cache
def get_default_model_for_provider(provider_name: str) -> Optional[str]:
    default_models = _get_provider_model()
    return default_models.get(provider_name, None)


def get_model_validation_message(provider) -> Optional[str]:
    # Check AWS Bedrock
    if provider == "aws_bedrock" and not config.aws_access_key_id:
        return "AWS Bedrock provider defined but AWS access key ID is not configured or empty."

    # Check Anthropic
    if provider == "anthropic" and not config.anthropic_api_key:
        return "Anthropic provider defined but Anthropic API key is not configured or empty."

    # Check OpenAI
    if provider == "openai" and not config.openai_api_key:
        return "OpenAI provider defined but OpenAI API key is not configured or empty."
    return None


def get_llm_base(model_id, provider):
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
            base_url=config.openai_api_base or None,
            api_key=config.openai_api_key,
            max_tokens=4096,
            streaming=config.streaming,
            stream_usage=True,
        )

    if provider == "vertexai":
        from langchain_google_vertexai.model_garden import ChatAnthropicVertex

        # https://cloud.google.com/vertex-ai/generative-ai/docs/partner-models/use-claude#regions
        # https://github.com/GoogleCloudPlatform/vertex-ai-samples/blob/439a686f16830a035e4b478223a9b5197496616d/notebooks/official/generative_ai/anthropic_claude_3_intro.ipynb
        if model_id == "claude-3-5-sonnet-v2@20241022":
            available_regions = ["us-east5", "europe-west1"]
        elif model_id == "claude-3-5-haiku@20241022":
            available_regions = ["us-east5"]
        elif model_id == "claude-3-5-sonnet@20240620":
            available_regions = ["us-east5", "europe-west1", "asia-southeast1"]
        elif model_id == "claude-3-opus@20240229":
            available_regions = ["us-east5"]
        elif model_id == "claude-3-haiku@20240307":
            available_regions = ["us-east5", "europe-west1", "asia-southeast1"]
        elif model_id == "claude-3-sonnet@20240229":
            available_regions = ["us-east5"]
        else:
            available_regions = ["us-east5"]
        return ChatAnthropicVertex(
            model=model_id,
            max_tokens=4096,
            max_retries=3,
            streaming=config.streaming,
            location=available_regions[0],
        )

    # Uses Litellm
    if provider == "litellm":
        return ChatLiteLLM(model=model_id)

    # Return no model
    return None


def get_llm():
    return get_llm_base(config.model, config.provider or get_inferred_provider())


def get_orchestrator_llm():
    model = config.orchestrator_model if config.orchestrator_model else config.model
    provider = config.orchestrator_model_provider or config.provider or get_inferred_provider()
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

    # There is no variable for detecting vertexai

    return "litellm"
