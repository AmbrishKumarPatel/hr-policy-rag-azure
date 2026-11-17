from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
import config
from embeddings import get_embedding

search_client = SearchClient(
    endpoint=config.AZURE_SEARCH_ENDPOINT,
    index_name=config.AZURE_SEARCH_INDEX_NAME,
    credential=AzureKeyCredential(config.AZURE_SEARCH_API_KEY),
)


def search(query, user_groups, top=3):
    """Sirf wahi chunks dhundta hai jo user ke groups dekh sakte hai."""
    # Security trimming: chunk ke groups me se koi ek bhi user ke groups me ho
    groups_text = ",".join(user_groups)
    security_filter = f"groups/any(g: search.in(g, '{groups_text}', ','))"

    vector_query = VectorizedQuery(
        vector=get_embedding(query),
        k_nearest_neighbors=top,
        fields="embedding",
    )

    results = search_client.search(
        search_text=query,               # keyword search
        vector_queries=[vector_query],   # vector search
        filter=security_filter,          # sirf allowed documents
        select=["source", "page", "content"],
        top=top,
    )

    return [
        {
            "source": r["source"],
            "page": r["page"],
            "content": r["content"],
            "score": r["@search.score"],
        }
        for r in results
    ]


if __name__ == "__main__":
    q = "What health insurance plans does Zava offer?"
    for groups in (["all"], ["hr"]):
        print("\nUser groups:", groups)
        for h in search(q, groups):
            print(" ", round(h["score"], 4), "|", h["source"], "| page", h["page"])