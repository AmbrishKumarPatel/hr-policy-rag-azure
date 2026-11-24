from azure.search.documents.models import VectorizedQuery
from azure_clients import get_search_client
from embeddings import get_embedding
search_client = get_search_client()

import os
# Search ka tarika: "hybrid" (default), "keyword", ya "vector"
SEARCH_MODE = os.getenv("SEARCH_MODE", "hybrid")

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

    use_keyword = SEARCH_MODE in ("hybrid", "keyword")
    use_vector = SEARCH_MODE in ("hybrid", "vector")

    results = search_client.search(
        search_text=query if use_keyword else None,
        vector_queries=[vector_query] if use_vector else None,
        filter=security_filter,
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