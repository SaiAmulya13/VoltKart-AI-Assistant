
def format_citations(citations):

    formatted = []

    for citation in citations:

        if citation.get("type") == "table":

            formatted.append({
                "type": "table",
                "tables": citation.get("tables", []),
                "computation": citation.get(
                    "computation",
                    ""
                )
            })

        elif citation.get("type") == "document":

            formatted.append({
                "type": "document",
                "filename": citation.get("filename"),
                "document_date": citation.get(
                    "document_date"
                ),
                "section": citation.get("section")
            })

    return formatted

def format_document_citations(sources):

    grouped_sources = {}

    for source in sources:

        filename = source["filename"]

        if filename not in grouped_sources:

            grouped_sources[filename] = {
                "filename": filename,
                "document_date": source["document_date"],
                "page_numbers": set(),
                "chunk_ids": []
            }

        # Add page number if available
        page = source.get("page")

        if page is not None:
            grouped_sources[filename]["page_numbers"].add(page)

        # Add chunk ID
        chunk_id = source.get("chunk_id")

        if chunk_id:
            grouped_sources[filename]["chunk_ids"].append(
                chunk_id
            )

    formatted_citations = []

    for source in grouped_sources.values():

        formatted_citations.append({
            "filename": source["filename"],
            "document_date": source["document_date"],
            "page_numbers": sorted(source["page_numbers"]),
            "chunk_ids": source["chunk_ids"]
        })

    return formatted_citations
