
import json
import numpy as np
import faiss

from backend.config import BASE_DIR


# --------------------------------
# 1. Vector database paths
# --------------------------------

VECTOR_STORE_DIR = BASE_DIR / "data" / "vector_store"

INDEX_PATH = VECTOR_STORE_DIR / "voltkart.index"

METADATA_PATH = VECTOR_STORE_DIR / "chunks.json"


# --------------------------------
# 2. Save vector database
# --------------------------------

def save_vector_store(index, chunks):

    VECTOR_STORE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    faiss.write_index(
        index,
        str(INDEX_PATH)
    )

    with open(
        METADATA_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            chunks,
            file,
            ensure_ascii=False,
            indent=4
        )


# --------------------------------
# 3. Build a new FAISS vector store
# --------------------------------

def build_vector_store(chunks, embeddings):

    if not chunks:
        raise ValueError("No document chunks provided.")

    if len(chunks) != len(embeddings):
        raise ValueError(
            "Chunks and embeddings count do not match."
        )

    embeddings = np.asarray(
        embeddings,
        dtype="float32"
    )

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

    save_vector_store(
        index,
        chunks
    )

    print(
        "FAISS vector database created successfully."
    )

    print("Total vectors:", index.ntotal)

    print("Vector dimensions:", dimension)

    return index


# --------------------------------
# 4. Load FAISS vector store
# --------------------------------

def load_vector_store():

    if not INDEX_PATH.exists():
        raise FileNotFoundError(
            "FAISS index not found."
        )

    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            "Chunk metadata not found."
        )

    index = faiss.read_index(
        str(INDEX_PATH)
    )

    with open(
        METADATA_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        chunks = json.load(file)

    if index.ntotal != len(chunks):
        raise ValueError(
            "FAISS index and metadata count do not match."
        )

    return index, chunks


# --------------------------------
# 5. Add chunks to existing FAISS
# --------------------------------

def add_chunks_to_vector_store(
    new_chunks,
    embeddings
):

    if not new_chunks:
        return 0

    if len(new_chunks) != len(embeddings):
        raise ValueError(
            "Chunks and embeddings count do not match."
        )

    embeddings = np.asarray(
        embeddings,
        dtype="float32"
    )

    # Check whether vector store already exists
    if INDEX_PATH.exists() and METADATA_PATH.exists():

        index, existing_chunks = load_vector_store()

    elif not INDEX_PATH.exists() and not METADATA_PATH.exists():

        dimension = embeddings.shape[1]

        index = faiss.IndexFlatIP(
            dimension
        )

        existing_chunks = []

    else:

        raise ValueError(
            "FAISS index and metadata files are inconsistent."
        )

    # Prevent duplicate chunks
    existing_ids = {
        chunk["chunk_id"]
        for chunk in existing_chunks
    }

    chunks_to_add = []
    embeddings_to_add = []

    for chunk, embedding in zip(
        new_chunks,
        embeddings
    ):

        if chunk["chunk_id"] in existing_ids:
            continue

        chunks_to_add.append(chunk)

        embeddings_to_add.append(embedding)

        existing_ids.add(
            chunk["chunk_id"]
        )

    if not chunks_to_add:

        print("No new chunks to add.")

        return 0

    embeddings_to_add = np.asarray(
        embeddings_to_add,
        dtype="float32"
    )

    if embeddings_to_add.shape[1] != index.d:

        raise ValueError(
            "Embedding dimension does not match FAISS index."
        )

    # Add new vectors without deleting existing ones
    index.add(
        embeddings_to_add
    )

    updated_chunks = (
        existing_chunks
        + chunks_to_add
    )

    save_vector_store(
        index,
        updated_chunks
    )

    print(
        f"Added {len(chunks_to_add)} new chunks."
    )

    print(
        f"Total vectors: {index.ntotal}"
    )

    return len(chunks_to_add)


# --------------------------------
# 6. Identify document family
# --------------------------------

def detect_document_family(question):

    question = question.lower()

    if any(word in question for word in [
        "return",
        "refund",
        "restocking",
        "gold member",
        "platinum member",
        "silver member"
    ]):

        return "Return & Refund Policy"

    elif any(word in question for word in [
        "warranty",
        "voltcare",
        "warranty claim"
    ]):

        return "VoltCare Warranty Terms"

    elif any(word in question for word in [
        "machine learning engineer",
        "job description",
        "salary",
        "hiring",
        "job location",
        "hybrid",
        "jd"
    ]):

        return "Machine Learning Engineer JD"

    elif any(word in question for word in [
        "store operations",
        "store notice"
    ]):

        return "Store Operations Notice"

    return None


# --------------------------------
# 7. Select latest document versions
# --------------------------------

def select_latest_versions(chunks):

    latest_dates = {}

    for chunk in chunks:

        family = chunk.get(
            "document_family",
            "Unknown Document"
        )

        document_date = chunk.get(
            "document_date"
        )

        if not document_date:
            continue

        if (
            family not in latest_dates
            or document_date > latest_dates[family]
        ):

            latest_dates[family] = document_date

    latest_chunks = []

    for chunk in chunks:

        family = chunk.get(
            "document_family",
            "Unknown Document"
        )

        document_date = chunk.get(
            "document_date"
        )

        # Keep undated documents searchable
        if not document_date:

            latest_chunks.append(chunk)

        # Keep only the latest dated version per family
        elif latest_dates.get(family) == document_date:

            latest_chunks.append(chunk)

    return latest_chunks


# --------------------------------
# 8. Search documents
# --------------------------------

def search_documents(
    question,
    top_k=5,
    latest_only=True,
    document_family=None
):

    question = question.strip()

    if not question:
        raise ValueError(
            "Question cannot be empty."
        )

    if top_k < 1:
        raise ValueError(
            "top_k must be at least 1."
        )

    # Load FAISS index and metadata
    index, chunks = load_vector_store()

    if index.ntotal == 0:
        return []

    # Load embedding model only when document search is requested
    from backend.services.embedding_service import model

    # Generate question embedding
    query_embedding = model.encode(
        [question],
        normalize_embeddings=True
    )

    query_embedding = np.asarray(
        query_embedding,
        dtype="float32"
    )

    # Search directly with FAISS
    # This avoids reconstructing the entire vector matrix
    distances, matched_indices = index.search(
        query_embedding,
        index.ntotal
    )

    # Store similarity scores by vector index
    score_by_index = {
        int(index_id): float(score)
        for index_id, score in zip(
            matched_indices[0],
            distances[0]
        )
        if index_id >= 0
    }

    if document_family is None:

        document_family = detect_document_family(
            question
        )

    candidate_indices = list(
        range(len(chunks))
    )

    # Filter by document family
    if document_family:

        candidate_indices = [
            i for i in candidate_indices
            if chunks[i].get("document_family")
            == document_family
        ]

    # Filter by latest document version
    if latest_only:

        candidate_chunks = [
            chunks[i]
            for i in candidate_indices
        ]

        latest_chunks = select_latest_versions(
            candidate_chunks
        )

        latest_ids = {
            chunk["chunk_id"]
            for chunk in latest_chunks
        }

        candidate_indices = [
            i for i in candidate_indices
            if chunks[i]["chunk_id"] in latest_ids
        ]

    # Sort by similarity score
    candidate_indices.sort(
        key=lambda i: score_by_index.get(
            i,
            float("-inf")
        ),
        reverse=True
    )

    results = []

    for i in candidate_indices[:top_k]:

        result = chunks[i].copy()

        result["similarity_score"] = score_by_index[i]

        results.append(result)

    return results
