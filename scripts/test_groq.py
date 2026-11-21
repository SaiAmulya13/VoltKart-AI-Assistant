
from groq import Groq
from backend.config import GROQ_API_KEY, GROQ_MODEL


# Check API key
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing from .env")


# Create Groq client
client = Groq(
    api_key=GROQ_API_KEY
)


# Send a question
response = client.chat.completions.create(

    model=GROQ_MODEL,

    messages=[
        {
            "role": "system",
            "content": "You are a helpful AI assistant."
        },
        {
            "role": "user",
            "content": "What is Artificial Intelligence?"
        }
    ]
)


# Display response
answer = response.choices[0].message.content

print("\nGroq API Response:\n")

print(answer)
