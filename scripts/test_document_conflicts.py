
from backend.services.document_service import load_all_documents
from backend.services.version_service import (
    get_latest_documents,
    group_documents_by_family
)

documents = load_all_documents()

grouped = group_documents_by_family(documents)
latest_documents = get_latest_documents(documents)

latest_by_family = {
    doc["document_family"]: doc
    for doc in latest_documents
}

print("\nDOCUMENT CONFLICT CHECK")
print("=======================")

for family, versions in grouped.items():

    latest = latest_by_family.get(family)

    print(f"\nFamily: {family}")

    if latest:
        print("Latest:", latest["filename"])
        print("Date:", latest["document_date"])

    print("Available versions:")

    for version in versions:
        print(
            "-",
            version["filename"],
            "|",
            version["document_date"]
        )

print("\nConflict inspection completed.")
