
from langchain_text_splitters import RecursiveCharacterTextSplitter


# ---------------------------------------
# 1. Configure text splitter
# ---------------------------------------

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    length_function=len,
    separators=["\n\n", "\n", ". ", " ", ""]
)


# ---------------------------------------
# 2. Split one document into chunks
# ---------------------------------------

def split_document(document):

    all_chunks = []

    chunk_number = 0

    filename = document["filename"]

    source_id = document.get(
        "source_id",
        filename
    )

    for section in document["content"]:

        text = section["text"].strip()

        if not text:
            continue

        chunks = text_splitter.split_text(text)

        for chunk in chunks:

            chunk_number += 1

            chunk_data = {
                "chunk_id": (
                    f"{source_id}_{chunk_number}"
                ),

                "source_id": source_id,

                "text": chunk,

                "filename": filename,

                "document_family": document[
                    "document_family"
                ],

                "document_date": document[
                    "document_date"
                ],

                "file_type": document[
                    "file_type"
                ],

                "page": section.get("page"),

                "chunk_number": chunk_number
            }

            all_chunks.append(chunk_data)

    return all_chunks


# ---------------------------------------
# 3. Split all documents
# ---------------------------------------

def split_all_documents(documents):

    all_chunks = []

    for document in documents:

        chunks = split_document(document)

        all_chunks.extend(chunks)

        print(
            f"{document['filename']} "
            f"-> {len(chunks)} chunks"
        )

    return all_chunks


# ---------------------------------------
# 4. Display chunk summary
# ---------------------------------------

def print_chunk_summary(chunks):

    print("\nCHUNK SUMMARY")
    print("-------------")

    print("Total chunks:", len(chunks))

    if not chunks:
        print("No document chunks were generated.")
        return

    first_chunk = chunks[0]

    print("\nFirst chunk details:")

    for key, value in first_chunk.items():

        print(f"{key}: {value}")

    print("\nFirst chunk text:")

    print(first_chunk["text"])
