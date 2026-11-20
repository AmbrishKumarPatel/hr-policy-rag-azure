import config
from azure_clients import get_openai_client

client = get_openai_client()


def get_embedding(text):
    """Ek text leta hai aur uska vector (numbers ki list) wapas deta hai."""
    response = client.embeddings.create(
        model=config.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        input=text,
    )
    return response.data[0].embedding


if __name__ == "__main__":
    v = get_embedding("How many leave days do employees get?")
    print("Vector ki length:", len(v))