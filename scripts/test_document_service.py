
from backend.services.document_service import (
    load_all_documents,
    get_document_summary
)


print("Loading VoltKart documents...\n")

documents = load_all_documents()

print("\nTotal documents loaded:", len(documents))

get_document_summary(documents)

print("\nDocument loading completed successfully!")
