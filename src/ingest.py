import json
import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
import config
from embeddings import client as openai_client   # embeddings.py wala client

# kaun si PDF kaun dekh sakta hai
FILE_GROUPS = {
    "employee_handbook.pdf": ["all", "hr"],
    "PerksPlus.pdf": ["all", "hr"],
    "Benefit_Options.pdf": ["hr"],
    "role_library.pdf": ["hr"],
}
BATCH_SIZE = 16

search_client = SearchClient(
    endpoint=config.AZURE_SEARCH_ENDPOINT,
    index_name=config.AZURE_SEARCH_INDEX_NAME,
    credential=AzureKeyCredential(config.AZURE_SEARCH_API_KEY),
)


def embed_batch(texts):
    """Kai texts ki embedding ek hi call me banata hai."""
    response = openai_client.embeddings.create(
        model=config.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        input=texts,
    )
    return [item.embedding for item in response.data]


# chunking.py ka output padhna
data_path = os.path.join(os.path.dirname(__file__), "..", "data", "chunks.json")
with open(data_path, encoding="utf-8") as f:
    chunks = json.load(f)

total_ok = 0
for i in range(0, len(chunks), BATCH_SIZE):
    batch = chunks[i:i + BATCH_SIZE]
    vectors = embed_batch([c["content"] for c in batch])

    docs = []
    for chunk, vector in zip(batch, vectors):
        docs.append({
            "id": chunk["id"],
            "source": chunk["source"],
            "page": chunk["page"],
            "content": chunk["content"],
            "groups": FILE_GROUPS.get(chunk["source"], ["hr"]),  # anjaan file sirf HR ko
            "embedding": vector,
        })

    result = search_client.upload_documents(documents=docs)
    ok = sum(1 for r in result if r.succeeded)
    total_ok += ok
    print(f"Batch {i // BATCH_SIZE + 1}: {ok}/{len(docs)} uploaded")

print("Total uploaded:", total_ok, "/", len(chunks))