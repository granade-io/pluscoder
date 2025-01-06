# Providers

PlusCoder support multiple providers by using LiteLLM, but we also support some native providers like OpenAI, Anthropic and VertexAI.

## Setup provider and model

You can specify `provider` and `model` options with different methods. Check how at the [Configuration](documentation/config.md#configuration-methods) section.

=== "CLI"
    ```bash
    pluscoder --provider <your-provider> --model <your-model>
    ```
=== "Python"
    ```python
    from pluscoder.agents.core import DeveloperAgent
    from pluscoder.type import AgentConfig

    # Setup provider and model when overriding agent defaults
    developer_agent: AgentConfig = DeveloperAgent.to_agent_config(provider="openai", model="gpt-4o")

    # Or update agent on the fly
    developer_agent.provider = <your-provider>
    developer_agent.model = <your-model>
    ```

!!! tip
    When no provider is specified, provider is inferred from credentials available in the environment variables. For example, if you have `OPENAI_API_KEY` set, OpenAI provider will be used, requiring only `model` option to run PlusCoder.

## Supported providers

### OpenAI

```bash
export OPENAI_API_KEY=<your_openai_api_key>
export OPENAI_API_BASE=<your_openai_api_base>
pluscoder --provider openai --model gpt-4o
```

### Anthropic

```bash
export ANTHROPIC_API_KEY=<your_anthropic_api_key>
pluscoder --provider anthropic --model claude-3-5-sonnet-20241022
```

### VertexAI

VertexAI provider requires gcloud CLI installed and authenticated.

Check available models at [VertexAI Model Garden](https://console.cloud.google.com/vertex-ai/model-garden).

```bash
pluscoder --provider vertexai --model claude-3-5-sonnet-v2@20241022
```

!!! note
    VertexAI requires to enable its API and models along proper IAM permissions before using it.

### Google

Google provider is used for Google AI Studio. 

```
export GOOGLE_API_KEY=<your_google_ai_studio_api_key>
pluscoder --provider google --model gemini-1.5-pro
```

### AWS Bedrock

AWS Bedrock provider requires AWS CLI installed and authenticated.

```
export AWS_ACCESS_KEY_ID=<your_aws_access_key_id>
export AWS_SECRET_ACCESS_KEY=<your_aws_secret_access_key>
export AWS_PROFILE=<your_aws_profile>
pluscoder --provider aws_bedrock --model anthropic.claude-3-5-sonnet-20241022-v2:0
```

### LiteLLM

You can use LiteLLM to access multiple providers and models.

```
export OPENAI_API_KEY=<your_openai_api_key>
pluscoder --provider litellm --model openai/gpt-4o
```