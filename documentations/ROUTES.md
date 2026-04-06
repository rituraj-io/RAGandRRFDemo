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
  "content": "string"
}
RESPONSE: { "doc_id": "uuid-string", "chunks": 5 }
NOTES: Chunks the text (200 char, 50 overlap) and stores each chunk in both ChromaDB (vector) and SQLite FTS5 (BM25). All chunks share the returned doc_id in metadata. The doc_id acts as the scope ID for subsequent search/chat requests.


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
NOTES: Returns all stored chunks.


### Delete Document

URL: /api/documents/{doc_id}
METHOD: DELETE
PAYLOAD: None
RESPONSE: { "deleted": "uuid-string" }
NOTES: Removes ALL chunks belonging to doc_id from both stores. Also deletes any chat tied to this doc_id.


---


## Search


### Search Documents

URL: /api/search?q={query}&mode={mode}&limit={limit}&doc_id={doc_id}&source={source}
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
- doc_id (optional): Scope search to chunks of a specific document.
- source (optional): Scope search to a data source. Use "sample" for HP books.
- Exactly one of doc_id or source is required. Omitting both returns 400.
- Hybrid mode uses Reciprocal Rank Fusion to merge vector and BM25 results.
- Sample data results include book_title in metadata.


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
PAYLOAD: {
  "doc_id": "uuid-string",   // for custom text scope
  "source": "sample"          // for sample data scope
}
RESPONSE: { "chat_id": "uuid-string" }
NOTES: Creates a new scoped chat. Exactly one of doc_id or source is required. Returns 400 if neither provided. Returns 503 if chat is disabled.


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
NOTES: Sends a message, retrieves context via scoped hybrid search (using the chat's stored doc_id or source), generates LLM response, saves both to chat history. Returns 503 if chat is disabled.


### Delete Chat

URL: /api/chat/{chat_id}
METHOD: DELETE
PAYLOAD: None
RESPONSE: { "deleted": "uuid-string" }
NOTES: Deletes chat and all its messages.
