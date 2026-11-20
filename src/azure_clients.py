from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
import config

# Aapki identity: laptop pe "az login" wali, Azure pe Managed Identity wali
credential = DefaultAzureCredential()

# Azure OpenAI ke liye token banane wala
token_provider = get_bearer_token_provider(
    credential, "https://cognitiveservices.azure.com/.default"
)


def get_openai_client():
    return AzureOpenAI(
        azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
        azure_ad_token_provider=token_provider,   # key ki jagah token
        api_version=config.AZURE_OPENAI_API_VERSION,
    )


def get_search_client():
    return SearchClient(
        endpoint=config.AZURE_SEARCH_ENDPOINT,
        index_name=config.AZURE_SEARCH_INDEX_NAME,
        credential=credential,                    # key ki jagah identity
    )


def get_index_client():
    return SearchIndexClient(
        endpoint=config.AZURE_SEARCH_ENDPOINT,
        credential=credential,
    )