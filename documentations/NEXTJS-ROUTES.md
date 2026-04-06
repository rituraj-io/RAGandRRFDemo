# Next.js Routes

All API routes are proxy pass-throughs to the Python backend.
The backend URL is configured via the `BACKEND_URL` environment variable (defaults to `http://localhost:8000`).


## Pages


### Dashboard

URL: /
NOTES: Landing page. Shows two feature cards linking to Search and Chat.


### Search & Retrieval

URL: /search
NOTES: Two-column layout. Left: paste content or load sample data. Right: search with filters (method, result count).


### Chat Interface

URL: /chat
NOTES: Conversational RAG interface. Start a new chat, send messages, view AI responses.


---


## API Proxy Routes


### Health

URL: /api/health
METHOD: GET
PROXIES TO: /health
RESPONSE: { "status": "ok", "chat_enabled": true|false }


---


### Documents


#### Ingest Document

URL: /api/documents
METHOD: POST
PROXIES TO: /api/documents
PAYLOAD: {
  "title": "string",
  "content": "string",
  "metadata": {},          // optional
  "permanent": false       // optional
}
RESPONSE: { "id": "uuid-string" }


#### List Documents

URL: /api/documents
METHOD: GET
PROXIES TO: /api/documents
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


#### Delete Document

URL: /api/documents/{docId}
METHOD: DELETE
PROXIES TO: /api/documents/{docId}
RESPONSE: { "deleted": "uuid-string" }


---


### Search


#### Search Documents

URL: /api/search?q={query}&mode={mode}&limit={limit}
METHOD: GET
PROXIES TO: /api/search?q={query}&mode={mode}&limit={limit}
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


---


### Chat


#### Chat Status

URL: /api/chat/status
METHOD: GET
PROXIES TO: /api/chat/status
RESPONSE: { "enabled": true|false }


#### Create Chat

URL: /api/chat
METHOD: POST
PROXIES TO: /api/chat
RESPONSE: { "chat_id": "uuid-string" }


#### List Chats

URL: /api/chat
METHOD: GET
PROXIES TO: /api/chat
RESPONSE: {
  "chats": [
    {
      "id": "uuid-string",
      "created_at": "ISO-8601",
      "preview": "First message text..."
    }
  ]
}


#### Get Chat History

URL: /api/chat/{chatId}
METHOD: GET
PROXIES TO: /api/chat/{chatId}
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


#### Send Message

URL: /api/chat/{chatId}/message
METHOD: POST
PROXIES TO: /api/chat/{chatId}/message
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


#### Delete Chat

URL: /api/chat/{chatId}
METHOD: DELETE
PROXIES TO: /api/chat/{chatId}
RESPONSE: { "deleted": "uuid-string" }
