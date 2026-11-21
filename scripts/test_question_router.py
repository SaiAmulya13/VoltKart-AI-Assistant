
from backend.services.question_router import identify_question_type


questions = [

    "Which store generated the highest revenue in 2025?",

    "Who are the top 3 customers?",

    "What is the return period for Gold members?",

    "What is the warranty coverage?",

    "What is the refund processing timeline?",

    "Which product has the most returns?",

    "What is the salary for Machine Learning Engineer?",

    "Explain artificial intelligence."
]


for question in questions:

    result = identify_question_type(question)

    print("\nQuestion:", question)

    print("Selected Engine:", result)
