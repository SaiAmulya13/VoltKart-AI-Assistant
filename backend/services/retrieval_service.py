
from backend.services.vector_store_service import search_documents


def retrieve_context(question, top_k=5):

    # Search relevant document chunks
    results = search_documents(
        question=question,
        top_k=top_k,
        latest_only=True
    )

    if not results:
        return {
            "context": "",
            "sources": []
        }

    context_parts = []

    sources = []

    for result in results:

        context_parts.append(
            result["text"]
        )

        source = {
            "filename": result["filename"],
            "document_date": result["document_date"],
            "page": result.get("page"),
            "chunk_id": result["chunk_id"]
        }

        if source not in sources:
            sources.append(source)

    context = "\n\n".join(context_parts)

    return {
        "context": context,
        "sources": sources
    }
