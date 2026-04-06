# Frontend User Flows


## Overview

Two main features: Search & Retrieval, and Chat.
Both share a common content-loading step before the user can interact.
The Python backend auto-ingests Harry Potter books on startup — sample data is always available.
Custom text must be ingested via POST /api/documents before it can be searched or chatted about.

**Data Isolation:** Search and chat are always scoped. Custom text uses a `doc_id` returned
from ingestion. Sample data uses `source=sample`. The two never mix, and different users'
custom text never leaks into each other's results.


---


## 1. Dashboard (Landing Page)

```
User lands on /
    |
    ├── Clicks "Search & Retrieval" card
    |       └── Navigate to /search
    |
    └── Clicks "Chat Interface" card
            └── Navigate to /chat
```


---


## 2. Search & Retrieval Flow

```
User lands on /search
    |
    ├── LEFT COLUMN: Content Setup
    |       |
    |       ├── [Default State] Empty textarea shown
    |       |       |
    |       |       ├── User pastes custom text
    |       |       |       ├── Character counter updates (limit: 10,000)
    |       |       |       ├── If over limit → counter turns red (still allowed)
    |       |       |       ├── On first search:
    |       |       |       |       ├── POST /api/documents { title, content }
    |       |       |       |       ├── Backend chunks text (200 char, 50 overlap)
    |       |       |       |       ├── Response: { doc_id, chunks }
    |       |       |       |       ├── Store doc_id in URL as query param (?doc_id=...)
    |       |       |       |       └── All subsequent searches include doc_id
    |       |       |       └── User clicks "Clear"
    |       |       |               ├── DELETE /api/documents/{doc_id} (if ingested)
    |       |       |               ├── Remove doc_id from URL
    |       |       |               └── Reset to empty textarea
    |       |       |
    |       |       └── User clicks "Load sample data" pill
    |       |               └── Transition to [Sample Loaded State]
    |       |
    |       └── [Sample Loaded State]
    |               ├── Textarea replaced with:
    |               |       ├── Green "Sample data loaded" badge
    |               |       ├── Description text
    |               |       ├── Numbered list of 7 Harry Potter books
    |               |       └── "Clear & enter your own" button (black, primary)
    |               |
    |               ├── Backend already has HP data (auto-ingested on startup)
    |               |       └── No POST /api/documents needed
    |               |       └── All searches use source=sample param instead of doc_id
    |               |
    |               └── User clicks "Clear & enter your own"
    |                       └── Transition back to [Default State]
    |
    |
    └── RIGHT COLUMN: Search + Results
            |
            ├── Search bar (type query, press Enter)
            |       └── On Enter:
            |               ├── GET /api/search?q={query}&mode={mode}&limit={limit}
            |               |       ├── Custom text: append &doc_id={doc_id}
            |               |       └── Sample data: append &source=sample
            |               └── Display results
            |
            ├── Filters
            |       ├── Method toggle: Vector | BM25 | Combined
            |       |       └── Maps to mode=vector | mode=bm25 | mode=hybrid
            |       └── Results count: 5 | 10 | 20
            |               └── Maps to limit=5 | limit=10 | limit=20
            |
            ├── [No Search Yet]
            |       └── Show placeholder icon + hint text
            |               ├── If no content: "Paste content on the left, then search here"
            |               └── If content present: "Type a query above and press Enter"
            |
            ├── [No Results]
            |       └── Show "No matching results found"
            |
            └── [Results Found]
                    ├── Show "{n} result(s) found" count
                    └── For each result:
                            ├── Rounded card with snippet text
                            ├── Score badge (font-mono)
                            ├── Chunk index number
                            └── If sample data: book_title tag from metadata
```


---


## 3. Chat Flow

```
User lands on /chat
    |
    ├── GET /api/chat/status
    |       ├── If enabled: false → show disabled message (chat requires LLM_API_KEY)
    |       └── If enabled: true → proceed
    |
    |
    ├── [LANDING STATE]
    |       ├── Chat icon + "Start a conversation" heading
    |       ├── Description text
    |       └── "New Chat" button (black, primary)
    |               └── Click → transition to [SETUP STATE]
    |
    |
    ├── [SETUP STATE] — Content Setup
    |       |
    |       ├── "Add your content" heading + description
    |       |
    |       ├── [Manual Input Mode]
    |       |       ├── "Load sample data" pill + "or paste your own below" hint
    |       |       ├── Textarea (10,000 char limit with counter)
    |       |       |       ├── User types/pastes content
    |       |       |       |       └── Character counter updates
    |       |       |       └── User clicks "Clear"
    |       |       |               └── Reset textarea
    |       |       |
    |       |       └── User clicks "Load sample data"
    |       |               └── Transition to [Sample Loaded Mode]
    |       |
    |       ├── [Sample Loaded Mode]
    |       |       ├── Rounded card with:
    |       |       |       ├── Green "Sample data loaded" badge
    |       |       |       ├── Description text
    |       |       |       ├── Numbered list of 7 Harry Potter books
    |       |       |       └── "Clear & enter your own" button (black, primary)
    |       |       |
    |       |       └── User clicks "Clear & enter your own"
    |       |               └── Transition back to [Manual Input Mode]
    |       |
    |       ├── "Start chatting" button
    |       |       ├── If no content → disabled + "Add content above to continue"
    |       |       └── If content present → enabled
    |       |               └── Click:
    |       |                       ├── If custom text:
    |       |                       |       ├── POST /api/documents { title, content }
    |       |                       |       ├── Backend chunks text (200 char, 50 overlap)
    |       |                       |       ├── Response: { doc_id, chunks }
    |       |                       |       └── Store doc_id
    |       |                       ├── If sample data:
    |       |                       |       └── No ingestion needed (already in backend)
    |       |                       ├── POST /api/chat { doc_id } or { source: "sample" }
    |       |                       |       └── Response: { chat_id }
    |       |                       |       └── Store chat_id
    |       |                       ├── Append doc_id (or source=sample) to URL as query param
    |       |                       └── Transition to [ACTIVE STATE]
    |       |
    |       └── "Cancel" link
    |               └── Transition back to [LANDING STATE]
    |
    |
    └── [ACTIVE STATE] — Chat Interface
            |
            ├── Header:
            |       ├── Back button → /
            |       ├── "Chat" title + content badge
            |       |       ├── "Sample data" (if sample loaded)
            |       |       └── "Custom content · {n} chars" (if custom)
            |       └── "New Chat" button
            |               └── Click:
            |                       ├── If custom content was ingested:
            |                       |       └── DELETE /api/documents/{doc_id}
            |                       |               (also deletes the chat server-side)
            |                       └── Transition to [LANDING STATE]
            |
            ├── Messages area:
            |       ├── [Empty] "Send a message to begin"
            |       |
            |       ├── User message → right-aligned bubble (dark bg, white text)
            |       |
            |       └── Assistant message → full-width text (no bubble)
            |               ├── Small icon + "Assistant" label
            |               └── Whitespace-preserved text block
            |
            ├── Typing indicator:
            |       └── Three pulsing dots (shown while waiting for response)
            |
            └── Input bar:
                    ├── Auto-expanding textarea
                    |       ├── Enter → send message
                    |       └── Shift+Enter → new line
                    ├── Send button (black when active, gray when disabled)
                    └── On send:
                            ├── POST /api/chat/{chat_id}/message { "message": "..." }
                            |       (backend looks up chat's scope automatically)
                            ├── Show typing indicator
                            ├── On response:
                            |       ├── Display assistant message
                            |       └── Optionally display sources (future)
                            └── On error:
                                    └── Show error state / retry option
```


---


## 4. Navigation

```
/  (Dashboard)
├── /search  (Search & Retrieval)
|       ├── /search?doc_id={id}     (custom text scoped)
|       ├── /search?source=sample   (sample data scoped)
|       └── Back button → /
└── /chat    (Chat Interface)
        ├── /chat?doc_id={id}       (custom text scoped)
        ├── /chat?source=sample     (sample data scoped)
        └── Back button → /
```


---


## 5. Backend API Calls Summary

| Frontend Action                  | HTTP Method | Endpoint                              | When                          |
|----------------------------------|-------------|---------------------------------------|-------------------------------|
| Health check                     | GET         | /health                               | App load (optional)           |
| Chat status check                | GET         | /api/chat/status                      | Chat page load                |
| Ingest custom text               | POST        | /api/documents                        | Before first search/chat      |
| List documents                   | GET         | /api/documents                        | Optional                      |
| Delete ingested document         | DELETE      | /api/documents/{doc_id}               | On clear/reset/new chat       |
| Search (custom)                  | GET         | /api/search?q=&doc_id=&mode=&limit=   | User presses Enter            |
| Search (sample)                  | GET         | /api/search?q=&source=sample&mode=&limit= | User presses Enter        |
| Create chat (custom)             | POST        | /api/chat { doc_id }                  | Start chatting button         |
| Create chat (sample)             | POST        | /api/chat { source: "sample" }        | Start chatting button         |
| Send chat message                | POST        | /api/chat/{chat_id}/message           | User sends message            |
| Get chat history                 | GET         | /api/chat/{chat_id}                   | Reload / reconnect (future)   |
| List chats                       | GET         | /api/chat                             | Chat list view (future)       |
| Delete chat                      | DELETE      | /api/chat/{chat_id}                   | New chat / cleanup            |


---


## 6. Scoping Rules

| Scenario              | Scope Param              | What Gets Searched             |
|-----------------------|--------------------------|--------------------------------|
| Custom text loaded    | doc_id={uuid}            | Only chunks from that document |
| Sample data loaded    | source=sample            | Only HP book chunks            |
| Neither selected      | —                        | 400 error (not allowed)        |

**Key rules:**
- Custom text and sample data never mix in results.
- Different users' custom text is isolated by doc_id — no cross-contamination.
- The doc_id is returned from POST /api/documents and must be stored by the frontend.
- For sample data, no ingestion call is needed — just pass source=sample on search/chat.
- Deleting a document (DELETE /api/documents/{doc_id}) also deletes any chat tied to it.
- Chat stores its scope at creation time — no need to pass doc_id on every message.


---


## 7. Gap Analysis — Frontend vs Backend

| Requirement                           | Backend Status  | Notes                                                     |
|---------------------------------------|-----------------|-----------------------------------------------------------|
| Ingest + chunk custom text            | Supported       | POST /api/documents (200 char chunks, 50 overlap)         |
| Auto-load HP sample data              | Supported       | Auto-ingested on backend startup                          |
| Scoped search (custom text)           | Supported       | GET /api/search with doc_id param                         |
| Scoped search (sample data)           | Supported       | GET /api/search with source=sample param                  |
| Search with vector/bm25/hybrid        | Supported       | mode param                                                |
| Search result limit (5/10/20)         | Supported       | limit param, range 1-100                                  |
| Search results include book_title     | Supported       | In metadata for sample data results only                  |
| Create scoped chat                    | Supported       | POST /api/chat with doc_id or source                      |
| Send message + scoped RAG response    | Supported       | POST /api/chat/{id}/message (auto-scoped search + LLM)    |
| Chat history                          | Supported       | GET /api/chat/{id}                                        |
| Delete custom docs on clear           | Supported       | DELETE /api/documents/{id} (also deletes tied chat)        |
| Chat enabled check                    | Supported       | GET /api/chat/status                                      |
| Unscoped search blocked               | Supported       | Returns 400 if neither doc_id nor source provided          |
| Unscoped chat blocked                 | Supported       | Returns 400 if neither doc_id nor source provided          |

### Key Notes

1. **Sample data needs no frontend ingestion** — backend auto-loads HP books on startup.
   Frontend just passes `source=sample` on search/chat requests.

2. **Custom text requires ingestion first** — frontend must POST /api/documents before
   searching or chatting. The returned `doc_id` is the scope — store it in URL query params.

3. **Chat requires LLM_API_KEY** — if not configured, POST routes return 503.
   Frontend should check /api/chat/status on page load and show appropriate messaging.

4. **Ingestion now chunks text** — POST /api/documents chunks the content into ~200 char
   overlapping pieces. Response includes `doc_id` and `chunks` count.

5. **Chat scope is stored server-side** — after creating a chat with doc_id or source,
   all subsequent messages automatically search within that scope. No need to pass
   doc_id on every message request.

6. **DELETE /api/documents/{doc_id} cascades** — removes all chunks from both stores
   AND deletes any chat tied to that doc_id. Frontend only needs one DELETE call on clear/reset.
