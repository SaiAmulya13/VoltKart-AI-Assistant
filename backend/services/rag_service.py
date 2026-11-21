
from groq import Groq

from backend.config import GROQ_API_KEY, GROQ_MODEL

from backend.services.retrieval_service import retrieve_context

from backend.services.citation_service import format_document_citations


# ==========================================
# 1. Create Groq Client
# ==========================================

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing.")

client = Groq(
    api_key=GROQ_API_KEY
)


# ==========================================
# 2. Generate Answer Using RAG
# ==========================================

def generate_rag_answer(question):

    # Step 1: Retrieve relevant document chunks

    retrieved_data = retrieve_context(
        question,
        top_k=5
    )

    context = retrieved_data["context"]

    sources = retrieved_data["sources"]


    # Step 2: Check whether context is available

    if not context.strip():

        return {
            "answer": (
                "I could not find relevant information "
                "in the available VoltKart documents."
            ),
            "citations": []
        }


    # Step 3: Create system prompt

    system_prompt = """
    You are VoltKart's AI business assistant.

    Answer questions using ONLY the provided document context.

    Instructions:

    1. Do not invent information.
    2. Do not use outside knowledge.
    3. If the answer is not available in the context,
       clearly say that the information is not available.
    4. Give clear and simple answers.
    5. Pay attention to document versions and dates.
    6. Do not mix outdated policy information with
       the latest policy.
    """


    # Step 4: Create user prompt

    user_prompt = f"""
    DOCUMENT CONTEXT:

    {context}

    USER QUESTION:

    {question}

    Answer the question using only the document context.
    """


    # Step 5: Send request to Groq

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

        temperature=0.2,

        max_tokens=500
    )


    # Step 6: Extract generated answer

    answer = response.choices[0].message.content


    # Step 7: Format and remove duplicate citations

    formatted_citations = format_document_citations(
        sources
    )


    # Step 8: Return answer and citations

    return {
        "answer": answer,
        "citations": formatted_citations
    }
