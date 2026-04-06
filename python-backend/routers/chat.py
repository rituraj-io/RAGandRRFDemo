"""
Chat router — create, message, list, and delete chats.

Only available when LLM_API_KEY is configured. Each chat is
scoped to either a doc_id (custom text) or source (sample data).
"""

from typing import Callable, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.chat_store import ChatStore
from services.chat import ChatService


# -- Request/Response models --

class ChatCreateRequest(BaseModel):
    """Request body for creating a chat."""
    doc_id: Optional[str] = None
    source: Optional[str] = None


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
    def create_chat(body: ChatCreateRequest):
        """Create a new scoped chat conversation."""
        if not chat_enabled:
            raise HTTPException(status_code=503, detail="Chat is not enabled. Set LLM_API_KEY in .env.")

        if not body.doc_id and not body.source:
            raise HTTPException(status_code=400, detail="Either doc_id or source is required.")

        chat_id = chat_store.create_chat(doc_id=body.doc_id, source=body.source)
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
        """Send a message and get an LLM response with scoped context."""
        if not chat_enabled or chat_service is None:
            raise HTTPException(status_code=503, detail="Chat is not enabled.")

        # Look up chat's scope
        scope = chat_store.get_scope(chat_id)

        # Get chat history
        history = chat_store.get_history(chat_id)

        # Search for relevant context within scope
        sources = hybrid_search_fn(
            body.message,
            limit=5,
            doc_id=scope.get("doc_id"),
            source=scope.get("source"),
        )

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
