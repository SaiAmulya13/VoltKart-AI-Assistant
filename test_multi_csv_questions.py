
from backend.services.multi_csv_service import (
    answer_multi_csv_question,
)


questions = [
    "Which store generated the highest revenue?",
    "Which products have the highest sales?",
    "Which customers placed the most orders?",
    "How many products were returned?",
    "What is the revenue from delivered orders?",
]


for question in questions:

    print("\n" + "=" * 60)
    print("Question:", question)

    result = answer_multi_csv_question(question)

    print("\nAnswer:")
    print(result["answer"])

    print("\nSources:")
    print(result["sources"])
