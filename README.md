# VoltKart AI Assistant

An AI-powered multi-source chat assistant that answers business questions using structured data (CSV files) and unstructured documents (PDF, DOCX, and TXT). It supports multi-table analytics, document-based question answering, citations, conversation history, and interactive visualizations.

## Project Overview

Businesses often store information across multiple CSV files, reports, and policy documents. Finding accurate answers requires manually searching documents and joining data from different sources.

VoltKart AI Assistant provides a conversational interface where users can upload business files and ask questions in natural language.

The assistant retrieves relevant information, performs data analysis, and generates answers with supporting sources.

## Problem Statement

Business data is distributed across multiple files and documents, making it difficult to:

- Retrieve information quickly
- Perform analysis across multiple tables
- Find relevant policies and document versions
- Understand business metrics
- Maintain context across follow-up questions

## Objectives

- Build an AI-powered conversational assistant.
- Support structured and unstructured data.
- Perform accurate multi-table data analysis.
- Retrieve relevant document information.
- Provide source citations for answers.
- Maintain conversation history.
- Generate visualizations from business data.

## Features

### 1. Multi-Source File Upload

Supports business data and documents such as:

- CSV
- PDF
- DOCX
- TXT

### 2. Multi-CSV Analytics

The assistant can analyze multiple related CSV files and answer questions requiring joins between tables.

Example questions:

- Which store had the highest revenue in 2025?
- Who were the top customers by spending?
- Which products were returned most often?
- What is the total refund amount by region?

### 3. Document-Based Question Answering

Uses uploaded documents to answer questions about:

- Return and refund policies
- Membership benefits
- Job descriptions
- Product policies
- Company notices

### 4. Retrieval-Augmented Generation (RAG)

The system retrieves relevant information from uploaded documents and uses it as context for generating responses.

### 5. Source Citations

Answers can include references to the source files used to generate the response, helping users verify the information.

### 6. Conversation Memory

Supports follow-up questions using previous conversation context.

### 7. Persistent Chat History

Conversation history is stored so users can reopen previous chats.

### 8. Interactive Visualizations

Supports business analytics visualizations such as:

- Bar charts
- Line charts
- Category-wise revenue
- Monthly sales trends

### 9. PDF Conversation Export

Allows users to export conversations as PDF files.

### 10. Web Search

When enabled, the assistant can use web search to retrieve external information and compare it with company data.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI |
| Programming Language | Python |
| LLM | Groq API |
| RAG Framework | LangChain |
| Embeddings | Sentence Transformers |
| Vector Database | FAISS |
| Data Processing | Pandas, NumPy |
| Machine Learning | Scikit-learn |
| Database | SQLite |
| Visualization | Plotly / Matplotlib |
| API Server | Uvicorn |

## System Architecture

```text
                 User
                  |
                  v
          Streamlit Frontend
                  |
                  v
           FastAPI Backend
                  |
                  v
           Question Router
                  |
       +----------+----------+
       |                     |
       v                     v
 Structured Data        Document RAG
       |                     |
       v                     v
 Multi-CSV Analysis     Retrieval Service
       |                     |
       v                     v
 Data Joins             FAISS Vector Store
       |                     |
       +----------+----------+
                  |
                  v
          Answer Generation
                  |
                  v
       Answer + Source Citations
                  |
                  v
          Streamlit Chat UI
```

## Project Structure

```text
voltKart_ai_assistant/
│
├── backend/
│   ├── main.py
│   ├── services/
│   │   ├── chat_service.py
│   │   ├── multi_csv_service.py
│   │   ├── question_router.py
│   │   ├── rag_service.py
│   │   ├── retrieval_service.py
│   │   ├── vector_store_service.py
│   │   ├── query_engine.py
│   │   └── document_service.py
│   │
│   └── ...
│
├── frontend/
│   └── app.py
│
├── tests/
│   └── test_multi_csv_service.py
│
├── data/
│   └── ...
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

*The structure above is a simplified overview. Your repository may contain additional files and folders.*

## Installation and Setup

### Prerequisites

- Python installed
- Git installed
- Groq API key
- Windows, Linux, or macOS

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
```

Navigate to the project:

```bash
cd voltKart_ai_assistant
```

Replace the repository URL with your actual GitHub repository URL.

### 2. Create a virtual environment

For Windows PowerShell:

```powershell
python -m venv .venv
```

Activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root.

Example:

```env
GROQ_API_KEY=your_groq_api_key
```

Replace the placeholder with your actual API key.

**Do not upload your `.env` file or API keys to GitHub.**

### 5. Start the backend

Open a terminal:

```bash
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Backend API:

```text
http://127.0.0.1:8000
```

### 6. Start the frontend

Open another terminal in the project directory and activate the virtual environment.

Run:

```bash
python -m streamlit run frontend/app.py
```

The Streamlit application will open in your browser.

## Example Questions

### Business Analytics

- Which store had the highest revenue in 2025?
- Who were the top 3 customers by spending?
- Which product was returned most often?
- What is the total refund amount by region?
- Show category-wise revenue as a bar chart.
- Show monthly smartphone sales as a line chart.

### Policy Questions

- What is the return window for Gold members?
- Are opened earbuds returnable?
- How long does a refund take?
- What is the restocking fee for smartphones?

### Follow-Up Questions

- Who were the top customers at that store?
- Show their spending details.
- Compare the results with another store.

## Running Tests

Run the multi-CSV service tests:

```bash
python -m pytest tests/test_multi_csv_service.py -v
```

## Security

- Store API keys in environment variables.
- Do not commit `.env` files.
- Avoid publishing confidential company data.
- Review uploaded files before sharing the repository publicly.

## Future Improvements

- Improve retrieval accuracy.
- Add more automated test coverage.
- Optimize vector-store memory usage.
- Improve deployment reliability.
- Add additional business analytics and visualizations.

## Author
Sai Amulya
