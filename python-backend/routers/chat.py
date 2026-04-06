"""
Chat router — create, message, list, and delete chats.

Only available when LLM_API_KEY is configured. Each chat
has a UUID, and history is stored in SQLite.
"""

from typing import Callable

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.chat_store import ChatStore
from services.chat import ChatService


# -- Request/Response models --

class MessageRequest(BaseModel):
    """Request body for sending a chat message."""
    message: str


class MessageResponse(BaseModel):
    """Response body after sending a chat message."""
    response: str
    sources: list[dict]


# -- Router factory --

def create_chat_router(
    chat_store: ChatStore,
    chat_service: ChatService | None,
    hybrid_search_fn: Callable,
    chat_enabled: bool,
) -> APIRouter:
    """Create the chat router with injected dependencies."""

    router = APIRouter(prefix="/api/chat", tags=["chat"])


    @router.get("/status")
    def get_chat_status():
        """Check if chat is enabled."""
        return {"enabled": chat_enabled}


    @router.post("", status_code=201)
    def create_chat():
        """Create a new chat conversation."""
        if not chat_enabled:
            raise HTTPException(status_code=503, detail="Chat is not enabled. Set LLM_API_KEY in .env.")

        chat_id = chat_store.create_chat()
        return {"chat_id": chat_id}


    @router.get("")
    def list_chats():
        """List all chat conversations."""
        chats = chat_store.list_chats()
        return {"chats": chats}


    @router.get("/{chat_id}")
    def get_chat(chat_id: str):
        """Get full chat history."""
        messages = chat_store.get_history(chat_id)
        return {"chat_id": chat_id, "messages": messages}


    @router.post("/{chat_id}/message", response_model=MessageResponse)
    def send_message(chat_id: str, body: MessageRequest):
        """Send a message and get an LLM response."""
        if not chat_enabled or chat_service is None:
            raise HTTPException(status_code=503, detail="Chat is not enabled.")

        # Get chat history
        history = chat_store.get_history(chat_id)

        # Search for relevant context
        sources = hybrid_search_fn(body.message, limit=5)

        # Generate LLM response
        response_text = chat_service.generate_response(
            message=body.message,
            history=history,
            sources=sources,
        )

        # Save messages to chat store
        chat_store.add_message(chat_id, role="user", content=body.message)
        chat_store.add_message(chat_id, role="assistant", content=response_text)

        return {"response": response_text, "sources": sources}


    @router.delete("/{chat_id}")
    def delete_chat(chat_id: str):
        """Delete a chat and all its messages."""
        chat_store.delete_chat(chat_id)
        return {"deleted": chat_id}


    return router
