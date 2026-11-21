
from backend.services.vector_store_service import search_documents


question = "What is the return period for Gold members?"

results = search_documents(
    question,
    top_k=5
)

print("\nQUESTION:", question)

print("\nRETRIEVED DOCUMENTS:")

for i, result in enumerate(results, start=1):

    print("\nResult:", i)

    print("Document:", result["filename"])

    print("Family:", result["document_family"])

    print("Date:", result["document_date"])

    print("Similarity:", result["similarity_score"])

    print("Content:", result["text"])


# Test historical retrieval

print("\n\nHISTORICAL SEARCH:")

historical_results = search_documents(
    "What is the return period for Gold members?",
    top_k=5,
    latest_only=False
)

for result in historical_results:

    print(
        result["filename"],
        result["document_date"]
    )
