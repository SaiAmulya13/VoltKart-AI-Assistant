
from backend.services.vector_store_service import search_documents


def retrieve_context(question, top_k=8):
    """
    Retrieve relevant document chunks and prepare context for the LLM.

    Each chunk includes its document name, date, page, and chunk ID
    so the LLM can distinguish information from different versions.
    """

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

    seen_chunks = set()
    seen_sources = set()

    for result in results:
        text = result.get("text", "").strip()

        if not text:
            continue

        # Avoid adding duplicate text chunks
        normalized_text = " ".join(text.lower().split())

        if normalized_text in seen_chunks:
            continue

        seen_chunks.add(normalized_text)

        filename = result.get("filename", "Unknown document")
        document_date = result.get("document_date", "Unknown date")
        page = result.get("page")
        chunk_id = result.get("chunk_id", "Unknown chunk")

        # Add source information directly before each chunk
        source_header = (
            f"[SOURCE: {filename}]\n"
            f"[DOCUMENT DATE: {document_date}]\n"
            f"[CHUNK ID: {chunk_id}]"
        )

        if page is not None:
            source_header += f"\n[PAGE: {page}]"

        context_parts.append(
            f"{source_header}\n"
            f"DOCUMENT TEXT:\n{text}"
        )

        # Keep unique source details for citations
        source_key = (
            filename,
            document_date,
            page,
            chunk_id
        )

        if source_key not in seen_sources:
            seen_sources.add(source_key)

            sources.append({
                "filename": filename,
                "document_date": document_date,
                "page": page,
                "chunk_id": chunk_id
            })

    context = "\n\n--- DOCUMENT CHUNK ---\n\n".join(context_parts)

    return {
        "context": context,
        "sources": sources
    }
