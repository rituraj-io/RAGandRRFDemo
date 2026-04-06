# API Routes


## Health

URL: /health
METHOD: GET
PAYLOAD: None
RESPONSE: { "status": "ok", "chat_enabled": true|false }
NOTES: Basic health check. Returns whether chat feature is enabled.


---


## Documents


### Ingest Document

URL: /api/documents
METHOD: POST
PAYLOAD: {
  "title": "string",
  "content": "string",
  "metadata": {},          // optional, defaults to {}
  "permanent": false       // optional, defaults to false
}
RESPONSE: { "id": "uuid-string" }
NOTES: Stores document in both ChromaDB (vector) and SQLite FTS5 (BM25). Permanent documents are excluded from 30-day auto-cleanup.


### List Documents

URL: /api/documents
METHOD: GET
PAYLOAD: None
RESPONSE: {
  "documents": [
    {
      "id": "uuid-string",
      "title": "string",
      "content": "string",
      "permanent": true|false,
      "metadata": {}
    }
  ]
}
NOTES: Returns all ingested documents.


### Delete Document

URL: /api/documents/{doc_id}
METHOD: DELETE
PAYLOAD: None
RESPONSE: { "deleted": "uuid-string" }
NOTES: Removes document from both vector and BM25 stores.


---


## Search


### Search Documents

URL: /api/search?q={query}&mode={mode}&limit={limit}
METHOD: GET
PAYLOAD: None (query params only)
RESPONSE: {
  "results": [
    {
      "id": "uuid-string",
      "title": "string",
      "content": "string",
      "score": 0.85,
      "metadata": {}
    }
  ]
}
NOTES:
- q (required): Search query string.
- mode (optional): "vector", "bm25", or "hybrid". Defaults to "hybrid".
- limit (optional): Number of results, 1-100. Defaults to 10.
- Hybrid mode uses Reciprocal Rank Fusion to merge vector and BM25 results.


---


## Chat

All chat routes require LLM_API_KEY to be set in .env. If not set, POST routes return 503.


### Chat Status

URL: /api/chat/status
METHOD: GET
PAYLOAD: None
RESPONSE: { "enabled": true|false }
NOTES: Check if chat feature is available.


### Create Chat

URL: /api/chat
METHOD: POST
PAYLOAD: None
RESPONSE: { "chat_id": "uuid-string" }
NOTES: Creates a new chat conversation. Returns 503 if chat is disabled.


### List Chats

URL: /api/chat
METHOD: GET
PAYLOAD: None
RESPONSE: {
  "chats": [
    {
      "id": "uuid-string",
      "created_at": "ISO-8601",
      "preview": "First message text..."
    }
  ]
}
NOTES: Returns all chats sorted by creation date (newest first).


### Get Chat History

URL: /api/chat/{chat_id}
METHOD: GET
PAYLOAD: None
RESPONSE: {
  "chat_id": "uuid-string",
  "messages": [
    {
      "role": "user"|"assistant",
      "content": "string",
      "created_at": "ISO-8601"
    }
  ]
}
NOTES: Returns full message history for a chat.


### Send Message

URL: /api/chat/{chat_id}/message
METHOD: POST
PAYLOAD: { "message": "string" }
RESPONSE: {
  "response": "LLM response text",
  "sources": [
    {
      "id": "uuid-string",
      "title": "string",
      "content": "string",
      "score": 0.85,
      "metadata": {}
    }
  ]
}
NOTES: Sends a message, retrieves context via hybrid search, generates LLM response, saves both to chat history. Returns 503 if chat is disabled.


### Delete Chat

URL: /api/chat/{chat_id}
METHOD: DELETE
PAYLOAD: None
RESPONSE: { "deleted": "uuid-string" }
NOTES: Deletes chat and all its messages.
