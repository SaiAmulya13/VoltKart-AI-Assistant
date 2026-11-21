
from sentence_transformers import SentenceTransformer


# ---------------------------------------
# 1. Load embedding model
# ---------------------------------------

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

print("Loading embedding model...")

model = SentenceTransformer(MODEL_NAME)

print("Embedding model loaded successfully!")


# ---------------------------------------
# 2. Generate embedding for one text
# ---------------------------------------

def generate_single_embedding(text):

    embedding = model.encode(
        text,
        normalize_embeddings=True
    )

    return embedding


# ---------------------------------------
# 3. Generate embeddings for all chunks
# ---------------------------------------

def generate_embeddings(chunks):

    if not chunks:
        return []

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    embeddings = model.encode(
        texts,
        batch_size=16,
        show_progress_bar=True,
        normalize_embeddings=True
    )

    return embeddings


# ---------------------------------------
# 4. Display embedding information
# ---------------------------------------

def print_embedding_summary(chunks, embeddings):

    print("\nEMBEDDING SUMMARY")
    print("-----------------")

    print("Total chunks:", len(chunks))

    print("Embedding shape:", embeddings.shape)

    print("Vector dimensions:", embeddings.shape[1])

    print("\nFirst chunk:")

    print(chunks[0]["text"])

    print("\nFirst embedding values:")

    print(embeddings[0][:10])
