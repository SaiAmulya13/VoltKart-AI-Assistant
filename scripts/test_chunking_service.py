
from backend.services.document_service import (
    load_all_documents
)

from backend.services.chunking_service import (
    split_all_documents,
    print_chunk_summary
)


print("Loading documents...\n")

documents = load_all_documents()

print("\nSplitting documents into chunks...\n")

chunks = split_all_documents(documents)

print_chunk_summary(chunks)

print("\nDocument chunking completed successfully!")
