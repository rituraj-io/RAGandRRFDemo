# RAG & RRF Demo

A full-stack Retrieval-Augmented Generation system that demonstrates how RAG works end-to-end — from chunking and indexing documents, to retrieving relevant context using hybrid search, to generating AI-powered responses grounded in that context.

Built with **Next.js 16**, **FastAPI**, **ChromaDB**, and **SQLite FTS5**.

> **Live demo:** [ragdemo.appexflow.com](https://ragdemo.appexflow.com)


---


## What It Does

### Search & Retrieval

Compare three retrieval strategies side-by-side on any text corpus:

| Strategy | How It Works |
|----------|-------------|
| **Vector Search** | Finds semantically similar content using sentence embeddings (all-MiniLM-L6-v2) |
| **BM25** | Classic keyword matching using SQLite FTS5 |
| **Hybrid (RRF)** | Combines both using Reciprocal Rank Fusion for balanced results |

Paste any text or load the included Harry Potter sample data, search, and see how each method ranks results differently.

### Chat Interface

Ask questions in natural language and get AI-generated answers grounded in retrieved context. The system retrieves the top 5 relevant chunks from your corpus and passes them to the LLM as context — a textbook RAG pipeline you can inspect and learn from.


---


## Architecture

```
                  ┌─────────────────────────────────────────┐
                  │              Next.js Frontend            │
                  │                                         │
                  │   /search ──── Vector / BM25 / Hybrid   │
                  │   /chat ───── RAG-powered conversation  │
                  │                                         │
                  │   /api/* ──── Proxy to backend          │
                  └──────────────────┬──────────────────────┘
                                     │
                              Docker Network
                                     │
                  ┌──────────────────┴──────────────────────┐
                  │            FastAPI Backend               │
                  │                                         │
                  │   Embedding ──── all-MiniLM-L6-v2       │
                  │   Vector DB ─── ChromaDB (cosine)       │
                  │   Keyword DB ── SQLite FTS5 (BM25)      │
                  │   Hybrid ────── Reciprocal Rank Fusion  │
                  │   Chat ──────── LangChain + Gemini      │
                  └─────────────────────────────────────────┘
```

Every document chunk is stored in **both** ChromaDB and SQLite FTS5. Search queries hit both stores and results are merged using RRF (k=60) for the hybrid mode.


---


## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose

### 1. Clone and configure

```bash
git clone https://github.com/rituraj-io/RAGandRRFDemo.git
cd RAGandRRFDemo
```

Copy the example environment files:

```bash
cp .env.example .env
cp python-backend/.env.example python-backend/.env
```

### 2. Start the services

```bash
docker compose up -d --build
```

This starts:

- **Frontend** on [localhost:3333](http://localhost:3333)
- **Backend** on port 8000 (internal only)

First startup takes a few minutes — the backend downloads the embedding model (~90MB). Subsequent restarts are fast (model is cached).

### 3. (Optional) Enable chat

To use the chat interface, add an LLM API key to `python-backend/.env`:

```env
LLM_API_KEY=your-google-api-key
LLM_MODEL=gemini-2.5-flash
```

Then restart the backend:

```bash
docker compose restart backend
```

### 4. (Optional) Expose via Cloudflare Tunnel

Add your tunnel token to `.env`:

```env
CLOUDFLARE_TUNNEL_TOKEN=your-token
```

Start with the tunnel profile:

```bash
docker compose --profile tunnel up -d
```


---


## Project Structure

```
RAGandRRFDemo/
├── docker-compose.yml          # Orchestrates all services
├── .env.example                # Root env template (tunnel token)
│
├── nextjs-code/                # Frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx        # Home — feature cards
│   │   │   ├── search/         # Search interface
│   │   │   ├── chat/           # Chat interface
│   │   │   └── api/            # Proxy routes to backend
│   │   └── lib/
│   │       ├── proxy.ts        # Backend proxy utility
│   │       └── api.ts          # Client-side API helpers
│   └── Dockerfile
│
├── python-backend/             # Backend
│   ├── main.py                 # FastAPI app + lifespan
│   ├── config.py               # Pydantic settings
│   ├── routers/
│   │   ├── documents.py        # Ingest & manage documents
│   │   ├── search.py           # Vector / BM25 / hybrid search
│   │   └── chat.py             # RAG chat sessions
│   ├── services/
│   │   ├── embedding.py        # Sentence-transformers wrapper
│   │   ├── vector_store.py     # ChromaDB operations
│   │   ├── bm25_store.py       # SQLite FTS5 operations
│   │   ├── hybrid_search.py    # Reciprocal Rank Fusion
│   │   ├── chat.py             # LLM integration
│   │   ├── chat_store.py       # Chat history persistence
│   │   ├── chunking.py         # Text chunking logic
│   │   ├── ingestion.py        # Sample data loader
│   │   └── cleanup.py          # 30-day data retention
│   ├── tests/
│   └── Dockerfile
│
└── documentations/             # Technical docs
```


---


## API Reference

All endpoints are proxied through the Next.js frontend at `/api/*`.

### Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/documents` | Ingest and chunk text |
| `GET` | `/api/documents` | List all documents |
| `DELETE` | `/api/documents/{id}` | Delete a document |

### Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/search?q=...&mode=vector\|bm25\|hybrid&limit=5` | Search documents |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/chat/status` | Check if chat is enabled |
| `POST` | `/api/chat` | Create a chat session |
| `POST` | `/api/chat/{id}/message` | Send a message |
| `GET` | `/api/chat/{id}` | Get chat history |
| `DELETE` | `/api/chat/{id}` | Delete a session |


---


## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4 |
| Backend | FastAPI, Uvicorn, Python 3.12 |
| Embeddings | Sentence Transformers (all-MiniLM-L6-v2) |
| Vector Store | ChromaDB (cosine similarity) |
| Keyword Store | SQLite FTS5 (BM25) |
| Hybrid Ranking | Reciprocal Rank Fusion (k=60) |
| LLM | Google Gemini 2.5 Flash via LangChain |
| Infrastructure | Docker Compose, Cloudflare Tunnel |


---


## Key Concepts

**Scoped search** — Each ingested document gets its own scope. Searches and chat sessions only retrieve chunks from the relevant document, preventing cross-contamination between different texts.

**Dual indexing** — Every chunk is stored in both ChromaDB (for semantic search) and SQLite FTS5 (for keyword search), enabling fair comparison and hybrid retrieval.

**Reciprocal Rank Fusion** — Merges ranked lists from different retrieval systems using the formula `1 / (k + rank)`. This gives a balanced ranking that leverages both semantic understanding and exact keyword matches.

**Automatic cleanup** — A background task runs every 24 hours and removes non-permanent documents older than 30 days to manage storage.


---


## License

This project is for educational and demonstration purposes.
