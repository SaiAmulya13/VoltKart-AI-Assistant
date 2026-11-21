
from backend.services.rag_service import generate_rag_answer


# User question
question = "What is the return period for Gold members?"


# Generate RAG answer
result = generate_rag_answer(question)


# Display question
print("\nUSER QUESTION:")
print(question)


# Display AI answer
print("\nAI GENERATED ANSWER:")
print(result["answer"])


# Display citations
print("\nCITATIONS:")

for citation in result["citations"]:

    print("\nFilename:", citation["filename"])

    print("Document Date:", citation["document_date"])

    print("Pages:", citation["page_numbers"])

    print("Chunks:")

    for chunk_id in citation["chunk_ids"]:

        print("  ", chunk_id)
