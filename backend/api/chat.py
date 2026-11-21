
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.chat_service import (
    create_chat,
    update_chat_title,
    save_message,
    get_chat_messages,
    get_all_chats,
    generate_chat_response,
    delete_empty_chats,
    rename_chat
)


# ============================================================
# ROUTER CONFIGURATION
# ============================================================

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


# ============================================================
# REQUEST MODELS
# ============================================================

class ChatRequest(BaseModel):
    chat_id: str
    message: str

    # Web Search setting from Streamlit
    web_search: bool = False


class RenameChatRequest(BaseModel):
    title: str


# ============================================================
# 1. CREATE A NEW CHAT
# ============================================================

@router.post("/new")
def new_chat():

    try:

        chat_id = create_chat()

        return {
            "success": True,
            "message": "New chat created successfully.",
            "chat_id": chat_id
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# 2. SEND MESSAGE AND GENERATE ANSWER
# ============================================================

@router.post("/")
def chat(request: ChatRequest):

    try:

        chat_id = request.chat_id
        message = request.message.strip()

        web_search = request.web_search

        # ----------------------------------------------------
        # VALIDATE MESSAGE
        # ----------------------------------------------------

        if not message:

            raise HTTPException(
                status_code=400,
                detail="Message cannot be empty."
            )

        # ----------------------------------------------------
        # GET PREVIOUS CONVERSATION HISTORY
        # ----------------------------------------------------

        history = get_chat_messages(chat_id)

        # ----------------------------------------------------
        # GENERATE CHAT TITLE FROM FIRST QUESTION
        # ----------------------------------------------------

        if len(history) == 0:

            update_chat_title(
                chat_id,
                message
            )

        # ----------------------------------------------------
        # SAVE USER MESSAGE
        # ----------------------------------------------------

        save_message(
            chat_id,
            "user",
            message
        )

        # ----------------------------------------------------
        # GENERATE RESPONSE
        # ----------------------------------------------------
        print("WEB SEARCH RECEIVED BY BACKEND:", request.web_search)
        result = generate_chat_response(
            message,
            chat_history=history,
            web_search=web_search
        )
        print("CHAT ENGINE USED:", result.get("engine"))

        # ----------------------------------------------------
        # EXTRACT ANSWER
        # ----------------------------------------------------

        answer = result.get(
            "answer",
            "Sorry, I could not generate an answer."
        )

        # ----------------------------------------------------
        # EXTRACT CITATIONS
        # ----------------------------------------------------

        citations = result.get(
            "citations",
            []
        )

        # ----------------------------------------------------
        # EXTRACT ANSWERING ENGINE
        # ----------------------------------------------------

        engine = result.get(
            "engine",
            "unknown"
        )

        # ----------------------------------------------------
        # SAVE ASSISTANT RESPONSE
        # ----------------------------------------------------

        save_message(
            chat_id,
            "assistant",
            answer,
            citations
        )

        # ----------------------------------------------------
        # RETURN RESPONSE
        # ----------------------------------------------------

        return {
            "success": True,
            "chat_id": chat_id,
            "answer": answer,
            "citations": citations,
            "engine": engine,
            "web_search": web_search
        }

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat: {str(e)}"
        )


# ============================================================
# 3. GET CONVERSATION HISTORY
# ============================================================

@router.get("/history/{chat_id}")
def chat_history(chat_id: str):

    try:

        messages = get_chat_messages(chat_id)

        return {
            "success": True,
            "chat_id": chat_id,
            "messages": messages
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving chat history: {str(e)}"
        )


# ============================================================
# 4. GET ALL CHATS
# ============================================================

@router.get("/list")
def list_chats():

    try:

        chats = get_all_chats()

        return {
            "success": True,
            "chats": chats
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving chats: {str(e)}"
        )


# ============================================================
# 5. DELETE EMPTY CONVERSATIONS
# ============================================================

@router.delete("/empty")
def remove_empty_chats():

    try:

        deleted_count = delete_empty_chats()

        return {
            "success": True,
            "message": "Empty chats deleted successfully.",
            "deleted_count": deleted_count
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Error deleting empty chats: {str(e)}"
        )


# ============================================================
# 6. RENAME AN EXISTING CONVERSATION
# ============================================================

@router.patch("/rename/{chat_id}")
def rename_existing_chat(
    chat_id: str,
    request: RenameChatRequest
):

    try:

        new_title = rename_chat(
            chat_id,
            request.title
        )

        return {
            "success": True,
            "message": "Chat renamed successfully.",
            "chat_id": chat_id,
            "title": new_title
        }

    except ValueError as e:

        error_message = str(e)

        if error_message == "Chat not found.":

            raise HTTPException(
                status_code=404,
                detail=error_message
            )

        raise HTTPException(
            status_code=400,
            detail=error_message
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Error renaming chat: {str(e)}"
        )
