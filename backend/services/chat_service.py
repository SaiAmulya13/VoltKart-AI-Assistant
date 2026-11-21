
import uuid
import json
import re
from datetime import datetime, timezone

from backend.database.db import get_connection

from backend.services.question_router import (
    identify_question_type
)

from backend.services.query_engine import (
    answer_question
)

from backend.services.rag_service import (
    generate_rag_answer
)

from backend.services.uploaded_csv_service import (
    answer_uploaded_csv_question
)

from backend.services.multi_csv_service import (
    answer_multi_csv_question
)


# ==========================================
# 1. Get current UTC time
# ==========================================

def current_time():
    return datetime.now(timezone.utc).isoformat()


# ==========================================
# 2. Create a new chat
# ==========================================

def create_chat(title="New Chat"):

    chat_id = str(uuid.uuid4())
    timestamp = current_time()

    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO chats
            (chat_id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                chat_id,
                title,
                timestamp,
                timestamp
            )
        )

        connection.commit()

    finally:
        connection.close()

    return chat_id


# ==========================================
# 3. Update chat title
# ==========================================

def update_chat_title(chat_id, first_question):

    title = " ".join(
        first_question.strip().split()
    )

    if len(title) > 45:
        title = title[:42].rstrip() + "..."

    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE chats
            SET title = ?, updated_at = ?
            WHERE chat_id = ?
            """,
            (
                title,
                current_time(),
                chat_id
            )
        )

        connection.commit()

    finally:
        connection.close()

    return title


# ==========================================
# 4. Save a message
# ==========================================

def save_message(
    chat_id,
    role,
    content,
    citations=None
):

    connection = get_connection()
    timestamp = current_time()

    try:
        cursor = connection.execute(
            """
            INSERT INTO messages
            (chat_id, role, content, citations, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                chat_id,
                role,
                content,
                json.dumps(citations or []),
                timestamp
            )
        )

        connection.execute(
            """
            UPDATE chats
            SET updated_at = ?
            WHERE chat_id = ?
            """,
            (
                timestamp,
                chat_id
            )
        )

        connection.commit()

        message_id = cursor.lastrowid

    finally:
        connection.close()

    return message_id


# ==========================================
# 5. Get messages for a chat
# ==========================================

def get_chat_messages(chat_id):

    connection = get_connection()

    try:
        messages = connection.execute(
            """
            SELECT message_id, role, content,
                   citations, created_at
            FROM messages
            WHERE chat_id = ?
            ORDER BY message_id
            """,
            (chat_id,)
        ).fetchall()

    finally:
        connection.close()

    result = []

    for message in messages:

        item = dict(message)

        try:
            item["citations"] = json.loads(
                item["citations"] or "[]"
            )

        except json.JSONDecodeError:
            item["citations"] = []

        result.append(item)

    return result


# ==========================================
# 6. Get all chats
# ==========================================

def get_all_chats():

    connection = get_connection()

    try:
        chats = connection.execute(
            """
            SELECT chat_id, title, created_at, updated_at
            FROM chats
            ORDER BY updated_at DESC
            """
        ).fetchall()

    finally:
        connection.close()

    return [
        dict(chat)
        for chat in chats
    ]


# ==========================================
# 7. Delete empty conversations
# ==========================================

def delete_empty_chats():

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            DELETE FROM chats
            WHERE NOT EXISTS (
                SELECT 1
                FROM messages
                WHERE messages.chat_id = chats.chat_id
            )
            """
        )

        deleted_count = cursor.rowcount

        connection.commit()

    finally:
        connection.close()

    return deleted_count


# ==========================================
# 8. Detect hybrid questions
# ==========================================

def is_hybrid_question(question):

    question_lower = question.lower()

    hybrid_keywords = [

        # Order eligibility + policy
        "is that allowed",
        "is it allowed",
        "would a restocking fee",
        "if it were within the window",
        "within the return window",
        "within the window",

        # Notice + order data
        "does the order data agree",
        "does the data agree",
        "store was closed",
        "closed in december",
        "according to the store notice",

        # Questions requiring policy and order details
        "order and policy",
        "order eligibility",
        "eligible for return",
    ]

    return any(
        keyword in question_lower
        for keyword in hybrid_keywords
    )


# ==========================================
# 9. Detect multi-CSV questions
# ==========================================

def is_multi_csv_question(question):

    question_lower = question.lower()

    # Store revenue and store ranking

    if (
        "store" in question_lower
        and any(
            word in question_lower
            for word in [
                "revenue",
                "sales",
                "highest",
                "top",
                "rank",
                "manager",
            ]
        )
    ):
        return True

    # Category revenue

    if (
        "category" in question_lower
        and any(
            word in question_lower
            for word in [
                "revenue",
                "sales",
                "units",
            ]
        )
    ):
        return True

    # Product revenue or sales

    if (
        "product" in question_lower
        and any(
            word in question_lower
            for word in [
                "revenue",
                "sales",
                "best selling",
                "returned",
                "return reason",
            ]
        )
    ):
        return True

    # Customer spending and orders

    if (
        "customer" in question_lower
        and any(
            phrase in question_lower
            for phrase in [
                "most orders",
                "highest orders",
                "top orders",
                "placed the most",
                "number of orders",
                "top 3",
                "top three",
                "by spend",
                "by spending",
                "spend at",
                "spending at",
                "spent the most",
                "bought a laptop",
                "home city",
                "platinum",
                "that store",
                "same store",
            ]
        )
    ):
        return True

    # Follow-up questions about the previous store

    if (
        any(
            phrase in question_lower
            for phrase in [
                "at that store",
                "at the same store",
                "from that store",
                "that store",
            ]
        )
        and any(
            word in question_lower
            for word in [
                "customer",
                "spent",
                "spend",
                "bought",
                "purchase",
            ]
        )
    ):
        return True

    # Return and refund analysis

    if any(
        phrase in question_lower
        for phrase in [
            "most returned",
            "returned most often",
            "most common return reason",
            "refund amount by region",
            "total refund amount by region",
            "refunds by region",
            "return count",
            "return quantity",
            "number of returns",
        ]
    ):
        return True

    # General return analysis

    if (
        "return" in question_lower
        and any(
            phrase in question_lower
            for phrase in [
                "how many",
                "returned",
                "refund",
                "count",
                "revenue",
                "most common",
            ]
        )
    ):
        return True

    # Delivered-order revenue

    if (
        "delivered" in question_lower
        and any(
            word in question_lower
            for word in [
                "revenue",
                "sales",
            ]
        )
    ):
        return True

    # Revenue or sales by city

    if (
        "city" in question_lower
        and any(
            word in question_lower
            for word in [
                "revenue",
                "sales",
            ]
        )
    ):
        return True

    # Average Order Value

    if any(
        phrase in question_lower
        for phrase in [
            "average order value",
            "average value of orders",
            "aov",
        ]
    ):
        return True

    # Units sold by month

    if (
        "units sold" in question_lower
        and any(
            word in question_lower
            for word in [
                "month",
                "monthly",
                "per month",
            ]
        )
    ):
        return True

    # Date-based revenue questions

    has_revenue_or_sales = (
        "revenue" in question_lower
        or "sales" in question_lower
    )

    if has_revenue_or_sales:

        month_names = [
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        ]

        if any(
            month in question_lower
            for month in month_names
        ):
            return True

        if any(
            phrase in question_lower
            for phrase in [
                "monthly",
                "month-wise",
                "by month",
                "month",
            ]
        ):
            return True

        if any(
            str(year) in question_lower
            for year in range(2000, 2101)
        ):
            return True

    return False


# ==========================================
# 10. Extract store context from chat history
# ==========================================


def get_context_store(chat_history=None):

    if not chat_history:
        return None

    for index in range(
        len(chat_history) - 1,
        -1,
        -1
    ):

        message = chat_history[index]

        if isinstance(message, dict):
            role = message.get("role", "")
            content = message.get("content", "")
        else:
            role = getattr(message, "role", "")
            content = getattr(message, "content", "")

        if role != "assistant":
            continue

        if not isinstance(content, str):
            continue

        previous_user_question = ""

        for previous_index in range(
            index - 1,
            -1,
            -1
        ):

            previous_message = chat_history[
                previous_index
            ]

            if isinstance(previous_message, dict):
                previous_role = previous_message.get(
                    "role", ""
                )
                previous_content = previous_message.get(
                    "content", ""
                )
            else:
                previous_role = getattr(
                    previous_message, "role", ""
                )
                previous_content = getattr(
                    previous_message, "content", ""
                )

            if previous_role == "user":
                previous_user_question = str(
                    previous_content
                ).lower()
                break

        store_question = (
            "store" in previous_user_question
            and any(
                phrase in previous_user_question
                for phrase in [
                    "revenue",
                    "highest",
                    "top",
                    "sales",
                    "manager",
                ]
            )
        )

        if not store_question:
            continue

        # Extract store name and stop before
        # words such as "generated" or "has".

        store_match = re.search(
            r"\b(VoltKart\s+[A-Za-z]+(?:\s+[A-Za-z]+)?)"
            r"(?=\s+(?:generated|has|had|with|was|is)\b"
            r"|[.\n]|$)",
            content,
            re.IGNORECASE
        )

        if store_match:
            return store_match.group(1).strip()

    return None


# ==========================================
# 11. Generate response using CSV or RAG
# ==========================================

def generate_chat_response(
    question,
    chat_history=None
):

    question_lower = question.lower()

    question_type = identify_question_type(
        question
    )

    # Get previous store name for follow-up questions

    context_store = get_context_store(
        chat_history
    )

    # --------------------------------------
    # Detect explicit uploaded CSV questions
    # --------------------------------------

    is_explicit_uploaded_csv = (
        ".csv" in question_lower
        or "uploaded csv" in question_lower
        or "uploaded file" in question_lower
        or "this csv" in question_lower
        or "the csv file" in question_lower
        or "columns available" in question_lower
    )

    # --------------------------------------
    # 1. Explicit uploaded CSV questions
    # --------------------------------------

    if is_explicit_uploaded_csv:

        try:

            result = answer_uploaded_csv_question(
                question
            )

            return {
                "answer": result["answer"],
                "citations": result.get(
                    "citations",
                    []
                ),
                "engine": "uploaded_csv"
            }

        except (
            FileNotFoundError,
            ValueError
        ) as error:

            return {
                "answer": str(error),
                "citations": [],
                "engine": "uploaded_csv"
            }

    # --------------------------------------
    # 2. Hybrid questions
    # Business data + company documents
    # --------------------------------------

    if (
        question_type == "hybrid"
        or is_hybrid_question(question)
    ):

        try:

            # Business data lookup with context

            csv_result = answer_multi_csv_question(
                question,
                context_store=context_store
            )

            # Retrieve company policy/document answer

            rag_result = generate_rag_answer(
                question
            )

            csv_answer = csv_result.get(
                "answer",
                ""
            )

            rag_answer = rag_result.get(
                "answer",
                ""
            )

            combined_answer = (
                "**Business data / order information:**\n\n"
                + str(csv_answer)
                + "\n\n"
                "**Company document / policy information:**\n\n"
                + str(rag_answer)
            )

            # Multi-CSV service returns sources
            # while RAG returns citations

            csv_citations = csv_result.get(
                "citations",
                csv_result.get(
                    "sources",
                    []
                )
            )

            rag_citations = rag_result.get(
                "citations",
                []
            )

            # Ensure citations are lists

            if not isinstance(csv_citations, list):
                csv_citations = [csv_citations]

            if not isinstance(rag_citations, list):
                rag_citations = [rag_citations]

            combined_citations = (
                csv_citations + rag_citations
            )

            # Remove duplicate citations

            unique_citations = []
            seen = set()

            for citation in combined_citations:

                citation_key = json.dumps(
                    citation,
                    sort_keys=True,
                    default=str
                )

                if citation_key not in seen:

                    seen.add(citation_key)

                    unique_citations.append(
                        citation
                    )

            return {
                "answer": combined_answer,
                "citations": unique_citations,
                "engine": "hybrid"
            }

        except (
            FileNotFoundError,
            ValueError,
            KeyError
        ) as error:

            return {
                "answer": (
                    "I could not complete the combined "
                    "business-data and document lookup.\n\n"
                    + str(error)
                ),
                "citations": [],
                "engine": "hybrid"
            }

    # --------------------------------------
    # 3. Multi-CSV questions
    # --------------------------------------

    if is_multi_csv_question(question):

        try:

            result = answer_multi_csv_question(
                question,
                context_store=context_store
            )

            return {
                "answer": result["answer"],
                "citations": result.get(
                    "sources",
                    result.get(
                        "citations",
                        []
                    )
                ),
                "engine": "multi_csv"
            }

        except (
            FileNotFoundError,
            ValueError,
            KeyError
        ) as error:

            return {
                "answer": str(error),
                "citations": [],
                "engine": "multi_csv"
            }

    # --------------------------------------
    # 4. Other uploaded CSV questions
    # --------------------------------------

    if question_type == "uploaded_csv":

        try:

            result = answer_uploaded_csv_question(
                question
            )

            return {
                "answer": result["answer"],
                "citations": result.get(
                    "citations",
                    []
                ),
                "engine": "uploaded_csv"
            }

        except (
            FileNotFoundError,
            ValueError
        ) as error:

            return {
                "answer": str(error),
                "citations": [],
                "engine": "uploaded_csv"
            }

    # --------------------------------------
    # 5. Predefined business CSV questions
    # --------------------------------------

    if question_type == "csv":

        result = answer_question(
            question,
            chat_history=chat_history
        )

        return {
            "answer": result["answer"],
            "citations": result.get(
                "citations",
                []
            ),
            "engine": "csv"
        }

    # --------------------------------------
    # 6. Document RAG questions
    # --------------------------------------

    if question_type == "rag":

        result = generate_rag_answer(
            question
        )

        return {
            "answer": result["answer"],
            "citations": result.get(
                "citations",
                []
            ),
            "engine": "rag"
        }

    # --------------------------------------
    # 7. Unknown questions
    # --------------------------------------

    return {
        "answer": (
            "I can answer questions about VoltKart's "
            "business data, uploaded CSV files and "
            "company documents.\n\n"
            "Try asking about sales, customers, products, "
            "orders, returns, policies, warranty information "
            "or uploaded CSV data."
        ),
        "citations": [],
        "engine": "unknown"
    }


# ==========================================
# 12. Rename an existing chat
# ==========================================

def rename_chat(chat_id, new_title):

    new_title = " ".join(
        new_title.strip().split()
    )

    if not new_title:
        raise ValueError(
            "Chat title cannot be empty."
        )

    if len(new_title) > 60:

        new_title = (
            new_title[:57].rstrip()
            + "..."
        )

    connection = get_connection()

    try:

        cursor = connection.execute(
            """
            UPDATE chats
            SET title = ?, updated_at = ?
            WHERE chat_id = ?
            """,
            (
                new_title,
                current_time(),
                chat_id
            )
        )

        connection.commit()

        updated = cursor.rowcount

    finally:
        connection.close()

    if updated == 0:
        raise ValueError(
            "Chat not found."
        )

    return new_title
