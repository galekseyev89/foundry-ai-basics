from azure.ai.contentsafety import ContentSafetyClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import OpenAI

from foundry_ai_basics.core.config import AppConfig


def create_openai_client(config: AppConfig) -> OpenAI:
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(), "https://ai.azure.com/.default"
    )
    return OpenAI(base_url=config.azure_openai_endpoint, api_key=token_provider)


def create_content_safety_client(config: AppConfig) -> ContentSafetyClient:
    return ContentSafetyClient(
        endpoint=config.content_safety_endpoint,
        credential=DefaultAzureCredential(),
    )
