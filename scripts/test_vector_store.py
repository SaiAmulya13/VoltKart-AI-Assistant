
from backend.services.document_service import (
    load_all_documents
)

from backend.services.chunking_service import (
    split_all_documents
)

from backend.services.embedding_service import (
    generate_embeddings
)

from backend.services.vector_store_service import (
    build_vector_store,
    search_documents
)


# ---------------------------------------
# Step 1: Load documents
# ---------------------------------------

print("Loading documents...")

documents = load_all_documents()


# ---------------------------------------
# Step 2: Create chunks
# ---------------------------------------

print("\nCreating document chunks...")

chunks = split_all_documents(documents)


# ---------------------------------------
# Step 3: Generate embeddings
# ---------------------------------------

print("\nGenerating embeddings...")

embeddings = generate_embeddings(chunks)


# ---------------------------------------
# Step 4: Build FAISS database
# ---------------------------------------

print("\nBuilding FAISS vector database...")

build_vector_store(
    chunks,
    embeddings
)


# ---------------------------------------
# Step 5: Search documents
# ---------------------------------------

question = (
    "What is the return period for Gold members?"
)

print("\nSearching for:", question)

results = search_documents(
    question,
    top_k=5
)


# ---------------------------------------
# Step 6: Display search results
# ---------------------------------------

print("\nTOP MATCHING DOCUMENT CHUNKS")
print("-----------------------------")

for i, result in enumerate(results, start=1):

    print(f"\nResult {i}")

    print("Filename:", result["filename"])

    print("Document date:", result["document_date"])

    print("Page:", result["page"])

    print("Similarity:", result["similarity_score"])

    print("Text:", result["text"])


print("\nFAISS testing completed successfully!")
