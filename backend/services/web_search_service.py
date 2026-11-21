
import os
import requests

from groq import Groq
from backend.config import GROQ_API_KEY, GROQ_MODEL, TAVILY_API_KEY


# Initialize Groq client
groq_client = Groq(
    api_key=GROQ_API_KEY
)


# Tavily API endpoint
TAVILY_URL = "https://api.tavily.com/search"


def search_web(query):
    """
    Search the internet using Tavily.
    Returns search results and source URLs.
    """

    tavily_api_key = TAVILY_API_KEY

    if not tavily_api_key:
        raise ValueError(
            "TAVILY_API_KEY is missing. "
            "Please add it to your environment."
        )

    payload = {
        "api_key": tavily_api_key,
        "query": query,
        "search_depth": "advanced",
        "max_results": 5,
        "include_answer": False
    }

    response = requests.post(
        TAVILY_URL,
        json=payload,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    return data.get("results", [])


def generate_web_search_answer(
    question,
    chat_history=None
):
    """
    Search the web and generate an answer using Groq.
    """

    # Step 1: Search the internet
    search_results = search_web(question)

    if not search_results:
        return {
            "answer": "I could not find relevant information on the web.",
            "citations": []
        }

    # Step 2: Prepare search context
    search_context = ""

    citations = []

    for index, result in enumerate(search_results, start=1):

        title = result.get("title", "Web source")
        content = result.get("content", "")
        url = result.get("url", "")

        search_context += (
            f"\nSource {index}\n"
            f"Title: {title}\n"
            f"Content: {content}\n"
            f"URL: {url}\n"
        )

        if url:
            citations.append({
                "title": title,
                "url": url
            })

    # Step 3: Generate answer using Groq
    prompt = f"""
You are VoltKart AI Assistant.

Answer the user's question using the web search results
provided below.

Instructions:
1. Use the search results as your source of information.
2. Do not invent facts or return-window policies.
3. If the results do not provide enough information,
   clearly say that the information could not be verified.
4. Explain the answer in simple, clear language.
5. Mention important conditions or exceptions if available.
6. Do not invent citations or URLs.

User question:
{question}

Web search results:
{search_context}
"""

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant that answers "
                    "questions using reliable web search results."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    answer = response.choices[0].message.content

    return {
        "answer": answer,
        "citations": citations
    }
