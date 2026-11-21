
from backend.services.chat_service import generate_chat_response

questions = [
    "Which store generated the highest revenue in 2025?",
    "What is the return period for Gold members?",
    "What is the refund processing timeline?",
    "Explain artificial intelligence."
]

for question in questions:

    print("\n" + "=" * 60)

    print("QUESTION:", question)

    result = generate_chat_response(question)

    print("\nSELECTED ENGINE:", result["engine"])

    print("\nANSWER:")
    print(result["answer"])

    print("\nCITATIONS:")

    for citation in result["citations"]:
        print(citation)
