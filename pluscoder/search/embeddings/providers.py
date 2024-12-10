"""Provider configuration mapping and utilities."""

from typing import Literal

from pluscoder.search.embeddings.models import CohereConfig
from pluscoder.search.embeddings.models import ProviderConfig
from pluscoder.search.embeddings.models import VertexAIConfig

SEARCH_QUERY_PROVIDER_CONFIGS = {
    "cohere": CohereConfig(
        input_type="search_query",
    ),
    "vertex_ai": VertexAIConfig(),
}

SEARCH_DOCUMENT_PROVIDER_CONFIGS = {
    "cohere": CohereConfig(
        input_type="search_document",
    ),
    "vertex_ai": VertexAIConfig(),
}

PROVIDER_CONFIGS = {
    "search_document": SEARCH_DOCUMENT_PROVIDER_CONFIGS,
    "search_query": SEARCH_QUERY_PROVIDER_CONFIGS,
}


def get_provider_config(
    model_name: str,
    task_type: Literal["search_document", "search_query"],
) -> ProviderConfig:
    """Get provider config based on model name."""
    if "vertex_ai" in model_name:
        config = PROVIDER_CONFIGS[task_type]["vertex_ai"]
    elif "cohere" in model_name:
        config = PROVIDER_CONFIGS[task_type]["cohere"]
    else:
        config = ProviderConfig()

    return config
