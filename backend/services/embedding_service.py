
from sentence_transformers import SentenceTransformer
import threading


# ---------------------------------------
# 1. Embedding model configuration
# ---------------------------------------

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_model = None

_model_lock = threading.Lock()


# ---------------------------------------
# 2. Load embedding model only when needed
# ---------------------------------------

def get_embedding_model():

    global _model

    if _model is None:

        with _model_lock:

            # Check again after acquiring the lock
            if _model is None:

                print("Loading embedding model...")

                _model = SentenceTransformer(
                    MODEL_NAME,
                    device="cpu"
                )

                print("Embedding model loaded successfully!")

    return _model


# ---------------------------------------
# 3. Lazy model wrapper
# ---------------------------------------
# This keeps compatibility with code that uses:
# from backend.services.embedding_service import model
#
# The actual model is loaded only when model.encode()
# is called.


class LazyEmbeddingModel:

    def encode(self, *args, **kwargs):

        actual_model = get_embedding_model()

        return actual_model.encode(
            *args,
            **kwargs
        )


model = LazyEmbeddingModel()


# ---------------------------------------
# 4. Generate embedding for one text
# ---------------------------------------

def generate_single_embedding(text):

    actual_model = get_embedding_model()

    embedding = actual_model.encode(
        text,
        normalize_embeddings=True
    )

    return embedding


# ---------------------------------------
# 5. Generate embeddings for all chunks
# ---------------------------------------

def generate_embeddings(chunks):

    if not chunks:
        return []

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    actual_model = get_embedding_model()

    embeddings = actual_model.encode(
        texts,
        batch_size=8,
        show_progress_bar=True,
        normalize_embeddings=True
    )

    return embeddings


# ---------------------------------------
# 6. Display embedding information
# ---------------------------------------

def print_embedding_summary(chunks, embeddings):

    print("\nEMBEDDING SUMMARY")
    print("-----------------")

    print("Total chunks:", len(chunks))

    print("Embedding shape:", embeddings.shape)

    print("Vector dimensions:", embeddings.shape[1])

    if not chunks:
        print("No chunks available.")
        return

    print("\nFirst chunk:")

    print(chunks[0]["text"])

    print("\nFirst embedding values:")

    print(embeddings[0][:10])
