
import streamlit as st
import requests
import json
import pandas as pd
import os

from backend.services.multi_csv_service import (
    build_multi_csv_dataset
)


# ============================================================
# CONFIGURATION
# ============================================================

API_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:8000"
).rstrip("/")


st.set_page_config(
    page_title="VoltKart AI Assistant",
    page_icon="⚡",
    layout="wide"
)


# ============================================================
# DASHBOARD DATA FUNCTION
# ============================================================

@st.cache_data
def load_dashboard_data():
    """
    Load predefined VoltKart CSV files
    and prepare the joined dataset for charts.
    """

    dataset = build_multi_csv_dataset()

    # Convert order_date into datetime format
    dataset["order_date"] = pd.to_datetime(
        dataset["order_date"],
        errors="coerce"
    )

    # Remove rows with invalid dates
    dataset = dataset[
        dataset["order_date"].notna()
    ].copy()

    return dataset


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def extract_data(response):
    """Extract data from a FastAPI response."""

    try:
        result = response.json()

    except Exception:
        return {}

    if isinstance(result, dict):
        return result.get("data", result)

    return result


def get_chat_id(response):
    """Extract chat_id from API response."""

    data = extract_data(response)

    if isinstance(data, dict):
        return data.get("chat_id")

    return None


def get_chat_list():
    """Fetch all chats from backend."""

    try:
        response = requests.get(
            f"{API_URL}/chat/list",
            timeout=10
        )

        response.raise_for_status()

        data = extract_data(response)

        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            return data.get("chats", [])

        return []

    except requests.exceptions.RequestException:
        return []


def get_chat_history(chat_id):
    """Fetch messages for a selected chat."""

    try:
        response = requests.get(
            f"{API_URL}/chat/history/{chat_id}",
            timeout=10
        )

        response.raise_for_status()

        data = extract_data(response)

        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            return data.get("messages", [])

        return []

    except requests.exceptions.RequestException as e:
        st.error(
            f"Unable to load chat history: {e}"
        )

        return []


def create_new_chat():
    """Create a new chat using FastAPI."""

    try:
        response = requests.post(
            f"{API_URL}/chat/new",
            timeout=10
        )

        response.raise_for_status()

        chat_id = get_chat_id(response)

        if chat_id:

            st.session_state.chat_id = chat_id
            st.session_state.messages = []
            st.session_state.chat_loaded = True

            st.rerun()

        else:

            st.sidebar.error(
                "Chat was created, but chat ID was not returned."
            )

    except requests.exceptions.RequestException as e:

        st.sidebar.error(
            f"Unable to create chat: {e}"
        )


# ============================================================
# MULTIPLE FILE UPLOAD FUNCTION
# ============================================================

def upload_files(uploaded_files):
    """
    Upload multiple selected files to FastAPI.

    The backend upload endpoint accepts one file per request,
    so each selected file is uploaded separately.
    """

    successful_uploads = 0
    failed_uploads = 0

    progress_bar = st.sidebar.progress(0)

    total_files = len(uploaded_files)

    for index, uploaded_file in enumerate(
        uploaded_files,
        start=1
    ):

        try:

            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type
                )
            }

            response = requests.post(
                f"{API_URL}/files/upload",
                files=files,
                timeout=180
            )

            response.raise_for_status()

            data = extract_data(response)

            message = data.get(
                "message",
                "File uploaded successfully"
            )

            st.sidebar.success(
                f"✅ {uploaded_file.name}: {message}"
            )

            successful_uploads += 1

        except requests.exceptions.RequestException as e:

            failed_uploads += 1

            st.sidebar.error(
                f"❌ Failed to upload "
                f"{uploaded_file.name}: {e}"
            )

        progress_bar.progress(
            index / total_files
        )

    progress_bar.empty()

    st.sidebar.info(
        f"Upload completed: "
        f"{successful_uploads} successful, "
        f"{failed_uploads} failed."
    )


# ============================================================
# CHAT MANAGEMENT FUNCTIONS
# ============================================================

def rename_chat(chat_id, new_title):
    """Rename a chat."""

    try:

        response = requests.patch(
            f"{API_URL}/chat/rename/{chat_id}",
            json={"title": new_title},
            timeout=10
        )

        if response.status_code == 200:

            st.sidebar.success(
                "Chat renamed successfully."
            )

            st.rerun()

        else:

            st.sidebar.error(
                f"Rename failed: {response.text}"
            )

    except requests.exceptions.RequestException as e:

        st.sidebar.error(
            f"Unable to rename chat: {e}"
        )


def delete_empty_chats():
    """Delete chats that contain no messages."""

    try:

        response = requests.delete(
            f"{API_URL}/chat/empty",
            timeout=10
        )

        response.raise_for_status()

        st.sidebar.success(
            "Empty chats deleted successfully."
        )

        st.rerun()

    except requests.exceptions.RequestException as e:

        st.sidebar.error(
            f"Unable to delete empty chats: {e}"
        )


# ============================================================
# CITATION DISPLAY
# ============================================================

def display_citations(citations):
    """Display citations returned by the backend."""

    if not citations:
        return

    with st.expander("📚 Sources / Citations"):

        if isinstance(citations, str):

            st.write(citations)

        elif isinstance(citations, list):

            for index, citation in enumerate(
                citations,
                start=1
            ):

                st.markdown(
                    f"**Source {index}**"
                )

                if isinstance(citation, dict):

                    for key, value in citation.items():

                        if value is not None:

                            display_key = (
                                key.replace("_", " ").title()
                            )

                            st.write(
                                f"**{display_key}:** {value}"
                            )

                else:

                    st.write(citation)

                st.divider()

        elif isinstance(citations, dict):

            st.json(citations)

        else:

            st.write(citations)


# ============================================================
# MESSAGE NORMALIZATION
# ============================================================

def normalize_message(message):
    """Convert backend message data into a displayable format."""

    if not isinstance(message, dict):

        return {
            "role": "assistant",
            "content": str(message),
            "citations": []
        }

    role = message.get(
        "role",
        "assistant"
    )

    content = (
        message.get("content")
        or message.get("message")
        or message.get("answer")
        or ""
    )

    citations = message.get(
        "citations",
        []
    )

    if isinstance(citations, str):

        try:
            citations = json.loads(citations)

        except Exception:
            pass

    return {
        "role": role,
        "content": content,
        "citations": citations
    }


# ============================================================
# SESSION STATE
# ============================================================

if "chat_id" not in st.session_state:
    st.session_state.chat_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_loaded" not in st.session_state:
    st.session_state.chat_loaded = False
# Web Search setting
if "web_search_enabled" not in st.session_state:
    st.session_state.web_search_enabled = False



# ============================================================
# BACKEND CONNECTION CHECK
# ============================================================

backend_connected = False

try:

    response = requests.get(
        f"{API_URL}/docs",
        timeout=3
    )

    if response.status_code == 200:
        backend_connected = True

except requests.exceptions.RequestException:

    backend_connected = False


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("⚡ VoltKart AI")

    st.caption(
        "Multi-Source AI Chat Assistant"
    )

    st.divider()

    # --------------------------------------------------------
    # NEW CHAT
    # --------------------------------------------------------

    if st.button(
        "➕ New Chat",
        use_container_width=True
    ):

        if backend_connected:

            create_new_chat()

        else:

            st.error(
                "Backend is not connected. Start FastAPI first."
            )

    st.divider()

    # --------------------------------------------------------
    # MULTIPLE FILE UPLOAD
    # --------------------------------------------------------

    st.subheader("📁 Upload Files")

    uploaded_files = st.file_uploader(
        "Select CSV, PDF, DOCX or TXT files",
        type=["csv", "pdf", "docx", "txt"],
        accept_multiple_files=True,
        key="file_uploader"
    )

    if uploaded_files:

        st.caption(
            f"{len(uploaded_files)} file(s) selected"
        )

        for uploaded_file in uploaded_files:

            st.write(
                f"📄 {uploaded_file.name}"
            )

        if st.button(
            "Upload Selected Files",
            use_container_width=True
        ):

            if backend_connected:

                upload_files(
                    uploaded_files
                )

            else:

                st.error(
                    "Backend is not connected. "
                    "Start FastAPI first."
                )

    st.caption(
    "Upload business data or documents "
    "for your assistant."
)

st.divider()

# --------------------------------------------------------
# WEB SEARCH TOGGLE
# --------------------------------------------------------

st.subheader("🌐 Web Search")

st.session_state.web_search_enabled = st.toggle(
    "Enable Web Search",
    value=st.session_state.web_search_enabled,
    key="web_search_toggle",
    help=(
        "When enabled, the assistant can search "
        "the internet for current information."
    )
)

if st.session_state.web_search_enabled:
    st.success("Web Search is ON")
else:
    st.caption("Web Search is OFF")

st.divider()

# --------------------------------------------------------
# CHAT HISTORY
# --------------------------------------------------------
    # --------------------------------------------------------
    # CHAT HISTORY
    # --------------------------------------------------------

st.subheader("💬 Chat History")

chats = get_chat_list()

if chats:

    for chat in chats:

        chat_id = chat.get(
                "chat_id"
            )

        title = chat.get(
                "title",
                "New Chat"
            )

        if not chat_id:
                continue

        button_label = title

        if chat_id == st.session_state.chat_id:

                button_label = f"📌 {title}"

        if st.button(
                button_label,
                key=f"chat_{chat_id}",
                use_container_width=True
            ):

                st.session_state.chat_id = chat_id

                st.session_state.messages = (
                    get_chat_history(chat_id)
                )

                st.session_state.chat_loaded = True

                st.rerun()

    else:

        st.caption(
            "No previous chats found."
        )

    st.divider()

    # --------------------------------------------------------
    # RENAME ACTIVE CHAT
    # --------------------------------------------------------

    if st.session_state.chat_id:

        with st.expander(
            "✏️ Rename Current Chat"
        ):

            new_title = st.text_input(
                "Enter new chat title",
                key="rename_title_input"
            )

            if st.button(
                "Rename Chat",
                use_container_width=True
            ):

                if new_title.strip():

                    rename_chat(
                        st.session_state.chat_id,
                        new_title.strip()
                    )

                else:

                    st.warning(
                        "Please enter a chat title."
                    )

    # --------------------------------------------------------
    # DELETE EMPTY CHATS
    # --------------------------------------------------------

    with st.expander(
        "🧹 Chat Cleanup"
    ):

        st.caption(
            "Delete chats that do not contain any messages."
        )

        if st.button(
            "Delete Empty Chats",
            use_container_width=True
        ):

            delete_empty_chats()


# ============================================================
# MAIN PAGE
# ============================================================

st.title(
    "🤖 VoltKart AI Assistant"
)

st.write(
    "Ask questions about VoltKart sales, customers, "
    "products, orders, returns, policies and warranty documents."
)


# ============================================================
# BACKEND STATUS
# ============================================================

if backend_connected:

    st.success(
        "Backend connected successfully."
    )

else:

    st.error(
        "Backend is not connected. Start FastAPI first."
    )


# ============================================================
# SALES DASHBOARD
# ============================================================

st.header("📊 Sales Dashboard")

try:

    dashboard_data = load_dashboard_data()

    if dashboard_data.empty:

        st.warning(
            "No valid sales data is available for the dashboard."
        )

    else:

        # ====================================================
        # CHART 1: MONTHLY REVENUE
        # ====================================================

        st.subheader("📈 Monthly Revenue")

        monthly_data = dashboard_data.copy()

        # Create Month column from order_date
        monthly_data["Month"] = (
            monthly_data["order_date"]
            .dt.to_period("M")
            .astype(str)
        )

        # Calculate total revenue for each month
        monthly_revenue = (
            monthly_data
            .groupby("Month")["net_revenue_inr"]
            .sum()
            .reset_index()
            .sort_values("Month")
        )

        monthly_revenue.columns = [
            "Month",
            "Revenue (INR)"
        ]

        # Display line chart
        st.line_chart(
            monthly_revenue,
            x="Month",
            y="Revenue (INR)"
        )

        st.caption(
            "Monthly revenue is calculated using order date "
            "and net revenue after discounts."
        )

        # ====================================================
        # CHART 2 AND CHART 3
        # ====================================================

        col1, col2 = st.columns(2)

        # ====================================================
        # CHART 2: REVENUE BY CATEGORY
        # ====================================================

        category_revenue = (
            dashboard_data
            .groupby(
                "category",
                dropna=False
            )["net_revenue_inr"]
            .sum()
            .reset_index()
            .sort_values(
                "net_revenue_inr",
                ascending=False
            )
        )

        # Replace missing category names
        category_revenue["category"] = (
            category_revenue["category"]
            .fillna("Unknown")
        )

        category_revenue.columns = [
            "Category",
            "Revenue (INR)"
        ]

        with col1:

            st.subheader("📦 Revenue by Category")

            st.bar_chart(
                category_revenue,
                x="Category",
                y="Revenue (INR)"
            )

        # ====================================================
        # CHART 3: TOP 5 STORES BY REVENUE
        # ====================================================

        store_revenue = (
            dashboard_data
            .groupby(
                ["store_name", "city"],
                dropna=False
            )["net_revenue_inr"]
            .sum()
            .reset_index()
            .sort_values(
                "net_revenue_inr",
                ascending=False
            )
            .head(5)
        )

        # Replace missing store and city names
        store_revenue["store_name"] = (
            store_revenue["store_name"]
            .fillna("Unknown Store")
        )

        store_revenue["city"] = (
            store_revenue["city"]
            .fillna("Unknown City")
        )

        # Create combined store name
        store_revenue["Store"] = (
            store_revenue["store_name"]
            + " - "
            + store_revenue["city"]
        )

        store_revenue.columns = [
            "Store Name",
            "City",
            "Revenue (INR)",
            "Store"
        ]

        with col2:

            st.subheader("🏬 Top 5 Stores by Revenue")

            st.bar_chart(
                store_revenue,
                x="Store",
                y="Revenue (INR)"
            )

except Exception as e:

    st.warning(
        f"Could not load sales dashboard: {e}"
    )


st.divider()


# ============================================================
# WELCOME SCREEN
# ============================================================

if not st.session_state.chat_id:

    st.info(
        "Click **New Chat** in the sidebar "
        "to start a conversation."
    )

    st.markdown(
        """
        ### You can ask questions about:

        - Sales and revenue
        - Customers and loyalty tiers
        - Products and pricing
        - Orders and returns
        - Return policies
        - Warranty documents
        - Uploaded CSV and document files
        """
    )


# ============================================================
# DISPLAY CHAT MESSAGES
# ============================================================

if st.session_state.chat_id:

    for raw_message in st.session_state.messages:

        message = normalize_message(
            raw_message
        )

        role = message["role"]

        if role not in [
            "user",
            "assistant"
        ]:

            role = "assistant"

        with st.chat_message(role):

            st.markdown(
                message["content"]
            )

            if role == "assistant":

                display_citations(
                    message["citations"]
                )


# ============================================================
# CHAT INPUT
# ============================================================

if st.session_state.chat_id:

    user_question = st.chat_input(
        "Ask your question..."
    )

    if user_question:

        if not backend_connected:

            st.error(
                "Backend is not connected. "
                "Start FastAPI first."
            )

        else:

            # Display user question

            with st.chat_message("user"):

                st.markdown(
                    user_question
                )

            # Send question to backend

            try:

                response = requests.post(
                    f"{API_URL}/chat/",
                    json={
                        "chat_id": st.session_state.chat_id,
                        "message": user_question,
                        "web_search": st.session_state.web_search_enabled
                    },
                    timeout=180
                )

                response.raise_for_status()

                result = extract_data(
                    response
                )

                answer = result.get(
                    "answer",
                    "Sorry, I could not generate an answer."
                )

                citations = result.get(
                    "citations",
                    []
                )

                engine = result.get(
                    "engine",
                    "unknown"
                )

                # Display assistant response

                with st.chat_message("assistant"):

                    st.markdown(
                        answer
                    )

                    st.caption(
                        f"Answering engine: {engine}"
                    )

                    display_citations(
                        citations
                    )

                # Refresh chat history

                st.session_state.messages = (
                    get_chat_history(
                        st.session_state.chat_id
                    )
                )

                st.rerun()

            except requests.exceptions.RequestException as e:

                st.error(
                    f"Unable to get response from backend: {e}"
                )

            except Exception as e:

                st.error(
                    f"An unexpected error occurred: {e}"
                )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "VoltKart AI Assistant | Powered by FastAPI, "
    "Streamlit, FAISS and Groq"
)
