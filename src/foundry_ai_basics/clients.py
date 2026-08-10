from azure.ai.contentsafety import ContentSafetyClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from openai import OpenAI

from foundry_ai_basics.config import AppConfig
from foundry_ai_basics.ai.mcp import MCPToolClient

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


def create_search_index_client(config: AppConfig) -> SearchIndexClient:
    return SearchIndexClient(
        endpoint=config.search_service_endpoint,
        credential=DefaultAzureCredential(),
    )


def create_search_client(config: AppConfig) -> SearchClient:
    return SearchClient(
        endpoint=config.search_service_endpoint,
        index_name=config.search_index_name,
        credential=DefaultAzureCredential(),
    )

def create_mcp_client(config: AppConfig):
    return MCPToolClient(
        server_url=config.mcp_server_url,
        api_key=config.mcp_api_key,
    )