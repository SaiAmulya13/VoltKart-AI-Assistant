
from groq import Groq

from backend.config import GROQ_API_KEY, GROQ_MODEL
from backend.services.retrieval_service import retrieve_context
from backend.services.citation_service import format_document_citations


if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing.")

client = Groq(api_key=GROQ_API_KEY)


def generate_rag_answer(question):
    """
    Generate an answer using retrieved document context only.
    """

    retrieved_data = retrieve_context(
        question=question,
        top_k=8
    )

    context = retrieved_data.get("context", "")
    sources = retrieved_data.get("sources", [])

    # No relevant document context found
    if not context.strip():
        return {
            "answer": (
                "I could not find relevant information in the "
                "uploaded documents to answer this question."
            ),
            "citations": []
        }

    # Remove duplicate context sections
    unique_context_parts = []
    seen_context = set()

    for part in context.split("\n\n--- DOCUMENT CHUNK ---\n\n"):
        cleaned_part = part.strip()

        if not cleaned_part:
            continue

        normalized_part = " ".join(
            cleaned_part.lower().split()
        )

        if normalized_part in seen_context:
            continue

        seen_context.add(normalized_part)
        unique_context_parts.append(cleaned_part)

    context = "\n\n--- DOCUMENT CHUNK ---\n\n".join(
        unique_context_parts
    )

    # Prepare source information
    source_details = []

    for source in sources:
        filename = source.get(
            "filename",
            "Unknown document"
        )

        document_date = source.get(
            "document_date",
            "Unknown date"
        )

        page = source.get("page")

        source_text = (
            f"Document: {filename}\n"
            f"Document date: {document_date}"
        )

        if page is not None:
            source_text += f"\nPage: {page}"

        source_details.append(source_text)

    source_information = "\n\n".join(source_details)

    system_prompt = """
You are VoltKart's AI customer support assistant.

Answer the user's question using ONLY the provided document context.

Follow these rules carefully:

1. Do not use outside knowledge.
2. Do not invent information that is not present in the documents.
3. If the documents do not contain the answer, clearly say that
   the information was not found.
4. Check document dates when answering questions about policies.
5. If two documents contain conflicting information, prefer the
   most recent applicable document when it clearly replaces the
   older policy.
6. Do not automatically assume that a newer document replaces
   every older document. It must address the same subject.
7. If an older document contains unique information and the
   newer document does not address that subject, the older
   information may still be used. Mention its document date.
8. Do not combine conflicting policy values from different
   versions into one answer.
9. If you cannot determine which policy applies, explain the
   uncertainty instead of guessing.
10. Give a direct, concise answer in simple language.
11. Do not mention a specific product, customer, or order unless
    the context supports it.
12. Do not claim that information is current unless the documents
    support that claim.
13. Ignore document content that is unrelated to the question.
14. Always provide a meaningful answer. Never return an empty
    response.
"""

    user_prompt = f"""
DOCUMENT CONTEXT:

{context}

DOCUMENT SOURCES:

{source_information}

USER QUESTION:

{question}

Answer the question using the document context and the rules
provided above.
"""

    answer = ""

    try:
        # First attempt
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            temperature=0.1,
            max_tokens=600
        )

        choice = response.choices[0]

        answer = (
            choice.message.content or ""
        ).strip()

        # Print diagnostic information if Groq returns blank
        if not answer:
            print("\n===== GROQ DEBUG =====")
            print("Finish reason:", choice.finish_reason)
            print("Model:", response.model)
            print(
                "Message content:",
                repr(choice.message.content)
            )
            print("======================\n")

            # Retry with a simpler prompt
            retry_prompt = f"""
Use only the following document context to answer the question.

If documents conflict, prefer the most recent applicable
document. Do not guess.

DOCUMENT CONTEXT:
{context}

QUESTION:
{question}

Give a short, direct answer.
"""

            retry_response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a document-based customer "
                            "support assistant. Answer only from "
                            "the provided context. Do not guess."
                        )
                    },
                    {
                        "role": "user",
                        "content": retry_prompt
                    }
                ],
                temperature=0.0,
                max_tokens=300
            )

            retry_choice = retry_response.choices[0]

            answer = (
                retry_choice.message.content or ""
            ).strip()

            if not answer:
                print("\n===== GROQ RETRY DEBUG =====")
                print(
                    "Finish reason:",
                    retry_choice.finish_reason
                )
                print("Model:", retry_response.model)
                print(
                    "Message content:",
                    repr(retry_choice.message.content)
                )
                print("============================\n")

    except Exception as error:
        print("Groq answer generation error:", error)

        answer = ""

    # Ensure the frontend never receives a blank answer
    if not answer:
        answer = (
            "I retrieved relevant documents, but I could not "
            "generate an answer from them. Please try asking "
            "the question in a different way."
        )

    # Format document citations
    formatted_citations = format_document_citations(
        sources
    )

    return {
        "answer": answer,
        "citations": formatted_citations
    }
