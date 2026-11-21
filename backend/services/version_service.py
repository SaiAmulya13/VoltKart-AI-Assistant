
from datetime import datetime
from collections import defaultdict


# ---------------------------------------
# 1. Group documents by family
# ---------------------------------------

def group_documents_by_family(documents):

    grouped_documents = defaultdict(list)

    for document in documents:

        family = document["document_family"]

        grouped_documents[family].append(document)

    return dict(grouped_documents)


# ---------------------------------------
# 2. Select the latest document version
# ---------------------------------------

def get_latest_version(documents):

    if not documents:
        return None

    valid_documents = [
        document
        for document in documents
        if document.get("document_date")
    ]

    if not valid_documents:
        return None

    latest_document = max(
        valid_documents,
        key=lambda document: datetime.strptime(
            document["document_date"],
            "%Y-%m-%d"
        )
    )

    return latest_document


# ---------------------------------------
# 3. Select latest version for each family
# ---------------------------------------

def get_latest_documents(documents):

    grouped_documents = group_documents_by_family(
        documents
    )

    latest_documents = []

    for family, family_documents in grouped_documents.items():

        latest = get_latest_version(
            family_documents
        )

        if latest:

            latest_documents.append(latest)

    return latest_documents


# ---------------------------------------
# 4. Display version information
# ---------------------------------------

def print_version_summary(documents):

    grouped = group_documents_by_family(documents)

    print("\nDOCUMENT VERSION SUMMARY")
    print("------------------------")

    for family, family_documents in grouped.items():

        latest = get_latest_version(
            family_documents
        )

        print(f"\nDocument Family: {family}")

        for document in sorted(
            family_documents,
            key=lambda d: d["document_date"] or ""
        ):

            status = (
                "LATEST VERSION"
                if document == latest
                else "OLD VERSION"
            )

            print(
                f"{document['filename']} "
                f"-> {status}"
            )
