
import uuid
import json
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


# ---------------------------------------
# Get current UTC time
# ---------------------------------------

def current_time():
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------
# 1. Create a new chat
# ---------------------------------------

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


# ---------------------------------------
# 2. Update chat title
# ---------------------------------------

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


# ---------------------------------------
# 3. Save a message
# ---------------------------------------

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


# ---------------------------------------
# 4. Get messages for a chat
# ---------------------------------------

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


# ---------------------------------------
# 5. Get all chats
# ---------------------------------------

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


# ---------------------------------------
# 6. Delete empty conversations
# ---------------------------------------

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


# ---------------------------------------
# 7. Identify Multi-CSV questions
# ---------------------------------------

def is_multi_csv_question(question):

    question_lower = question.lower()

    # -----------------------------------------
    # 1. Store revenue or sales questions
    # -----------------------------------------

    if (
        "store" in question_lower
        and (
            "revenue" in question_lower
            or "sales" in question_lower
        )
    ):
        return True

    # -----------------------------------------
    # 2. Product category revenue or sales
    # -----------------------------------------

    if (
        "category" in question_lower
        and (
            "revenue" in question_lower
            or "sales" in question_lower
        )
    ):
        return True

    # -----------------------------------------
    # 3. Product revenue or sales questions
    # -----------------------------------------

    if (
        "product" in question_lower
        and (
            "revenue" in question_lower
            or "sales" in question_lower
            or "best selling" in question_lower
        )
    ):
        return True

    # -----------------------------------------
    # 4. Customer order-count questions
    # -----------------------------------------

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
            ]
        )
    ):
        return True

    # -----------------------------------------
    # 5. Return questions
    # -----------------------------------------

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
            ]
        )
    ):
        return True

    # -----------------------------------------
    # 6. Delivered-order revenue
    # -----------------------------------------

    if (
        "delivered" in question_lower
        and (
            "revenue" in question_lower
            or "sales" in question_lower
        )
    ):
        return True

    # -----------------------------------------
    # 7. Revenue or sales by city
    # -----------------------------------------

    if (
        "city" in question_lower
        and (
            "revenue" in question_lower
            or "sales" in question_lower
        )
    ):
        return True

    # -----------------------------------------
    # 8. Average Order Value (AOV)
    # -----------------------------------------

    if (
        "average order value" in question_lower
        or "average value of orders" in question_lower
        or "aov" in question_lower
    ):
        return True

    # -----------------------------------------
    # 9. Date-based revenue questions
    # -----------------------------------------

    has_revenue_or_sales = (
        "revenue" in question_lower
        or "sales" in question_lower
    )

    if has_revenue_or_sales:

        # Month names

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

        # Monthly revenue questions

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

        # Questions containing a year

        if any(
            str(year) in question_lower
            for year in range(2000, 2101)
        ):
            return True

    # -----------------------------------------
    # Unsupported multi-CSV question
    # -----------------------------------------

    return False


# ---------------------------------------
# 8. Generate response using CSV or RAG
# ---------------------------------------

def generate_chat_response(
    question,
    chat_history=None
):

    question_lower = question.lower()

    # Identify question type

    question_type = identify_question_type(
        question
    )

    # Detect explicit uploaded CSV questions

    is_explicit_uploaded_csv = (
        ".csv" in question_lower
        or "uploaded csv" in question_lower
        or "uploaded file" in question_lower
        or "this csv" in question_lower
        or "the csv file" in question_lower
        or "columns available" in question_lower
    )

    # ---------------------------------------
    # 1. Explicit uploaded CSV questions
    # ---------------------------------------

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

    # ---------------------------------------
    # 2. Multi-CSV questions
    # IMPORTANT: This must come before the
    # generic CSV routes.
    # ---------------------------------------

    if is_multi_csv_question(question):

        try:
            result = answer_multi_csv_question(
                question
            )

            return {
                "answer": result["answer"],
                "citations": result.get(
                    "sources",
                    []
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

    # ---------------------------------------
    # 3. Other uploaded CSV questions
    # ---------------------------------------

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

    # ---------------------------------------
    # 4. Predefined business CSV questions
    # ---------------------------------------

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

    # ---------------------------------------
    # 5. Document RAG questions
    # ---------------------------------------

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

    # ---------------------------------------
    # 6. Unsupported questions
    # ---------------------------------------

    return {
        "answer": (
            "I can answer questions about VoltKart's "
            "business data, uploaded CSV files and "
            "company documents.\n\n"
            "Try asking about sales, customers, products, "
            "orders, returns, policies, warranty information "
            "or the data in your uploaded CSV."
        ),
        "citations": [],
        "engine": "unknown"
    }


# ---------------------------------------
# 9. Rename an existing chat
# ---------------------------------------

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
