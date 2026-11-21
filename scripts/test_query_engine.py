
from backend.services.query_engine import answer_question


questions = [

    "Which store had the highest revenue in 2025, and who manages it?",

    "Who were the top 3 customers by spend at that store in 2025?",

    "Which product was returned most often, and what is its most common return reason?",

    "How many Platinum customers whose home city is Bengaluru bought a laptop in Q1 2026? Name them.",

    "What is the total refund amount by region?"

]


history = []

for question in questions:

    print("\n" + "=" * 70)

    print("QUESTION:")
    print(question)

    result = answer_question(
        question,
        history
    )

    print("\nANSWER:")
    print(result["answer"])

    print("\nCITATIONS:")
    print(result["citations"])

    # Simulate previous assistant response
    history.append({
        "role": "assistant",
        "content": result["answer"],
        "citations": result["citations"]
    })
