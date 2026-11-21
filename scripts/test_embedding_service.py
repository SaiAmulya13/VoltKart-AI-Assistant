
from backend.services.document_service import (
    load_all_documents
)

from backend.services.chunking_service import (
    split_all_documents
)

from backend.services.embedding_service import (
    generate_embeddings,
    print_embedding_summary
)


# Load documents
print("Loading documents...")

documents = load_all_documents()


# Split documents into chunks
print("\nCreating chunks...")

chunks = split_all_documents(documents)


# Generate embeddings
print("\nGenerating embeddings...")

embeddings = generate_embeddings(chunks)


# Display results
print_embedding_summary(
    chunks,
    embeddings
)

print("\nEmbedding generation completed successfully!")
