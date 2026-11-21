
from backend.services.document_service import load_all_documents

from backend.services.version_service import (
    get_latest_documents,
    print_version_summary
)


documents = load_all_documents()

print_version_summary(documents)

latest_documents = get_latest_documents(documents)

print("\nLATEST DOCUMENTS")
print("----------------")

for document in latest_documents:

    print(
        document["document_family"],
        "->",
        document["filename"]
    )

print("\nVersion management test completed!")
