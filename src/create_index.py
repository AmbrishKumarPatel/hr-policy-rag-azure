from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
)
import config

index_client = SearchIndexClient(
    endpoint=config.AZURE_SEARCH_ENDPOINT,
    credential=AzureKeyCredential(config.AZURE_SEARCH_API_KEY),
)

fields = [
    # har chunk ki unique pehchaan
    SimpleField(name="id", type=SearchFieldDataType.String, key=True),
    # kaun si PDF se aaya (citation ke liye)
    SimpleField(name="source", type=SearchFieldDataType.String, filterable=True),
    # kaun se page se aaya (citation ke liye)
    SimpleField(name="page", type=SearchFieldDataType.Int32, filterable=True),
    # chunk ka text, isme keyword search hogi
    SearchableField(name="content", type=SearchFieldDataType.String),
    # kaun se groups ye chunk dekh sakte hai (security trimming)
    SimpleField(
        name="groups",
        type=SearchFieldDataType.Collection(SearchFieldDataType.String),
        filterable=True,
    ),
    # 1536 numbers ka vector
    SearchField(
        name="embedding",
        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
        searchable=True,
        vector_search_dimensions=1536,
        vector_search_profile_name="vector-profile",
    ),
]

vector_search = VectorSearch(
    algorithms=[HnswAlgorithmConfiguration(name="hnsw-config")],
    profiles=[
        VectorSearchProfile(name="vector-profile", algorithm_configuration_name="hnsw-config")
    ],
)

index = SearchIndex(
    name=config.AZURE_SEARCH_INDEX_NAME,
    fields=fields,
    vector_search=vector_search,
)
if config.AZURE_SEARCH_INDEX_NAME in list(index_client.list_index_names()):
    index_client.delete_index(config.AZURE_SEARCH_INDEX_NAME)
    print("Purana index delete kiya")
result = index_client.create_or_update_index(index)
print("Index ban gaya:", result.name)