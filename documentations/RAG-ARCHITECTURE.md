# RAG Architecture — How Search & Retrieval Works

> A walkthrough of how queries travel through the system, how sample data (Harry Potter books) gets ingested, and how BM25 + Vector Search combine to find the right answers.

---

## The Big Picture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER SENDS A QUERY                           │
│                  "What happened to Dumbledore?"                     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │     FastAPI Backend     │
              │   /api/search or chat   │
              └────────────┬───────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
   ┌──────────────────┐     ┌──────────────────┐
   │   Vector Search   │     │   BM25 Search     │
   │   (Meaning)       │     │   (Keywords)      │
   │                   │     │                   │
   │  "Understands     │     │  "Finds exact     │
   │   that 'died'     │     │   word matches    │
   │   relates to      │     │   like             │
   │   'killed' and    │     │   'Dumbledore'    │
   │   'death'"        │     │   in the text"    │
   └────────┬─────────┘     └────────┬──────────┘
            │                         │
            └────────────┬────────────┘
                         │
                         ▼
            ┌─────────────────────────┐
            │  Reciprocal Rank Fusion  │
            │  (Merges both results)   │
            └────────────┬────────────┘
                         │
                         ▼
            ┌─────────────────────────┐
            │   Top results returned   │
            │   (best of both worlds)  │
            └─────────────────────────┘
```

---


## Step 0 — Sample Data Ingestion (Happens at Startup)

Before any search can happen, the Harry Potter books need to be chunked, embedded, and stored. This runs **automatically every time the app starts** and is **idempotent** — it skips books that are already fully ingested.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         APP STARTS UP                                    │
└──────────────────────────┬───────────────────────────────────────────────┘
                           │
                           ▼
             ┌──────────────────────────┐
             │  Load 7 HP book .txt     │
             │  files from data/HP-books │
             └────────────┬─────────────┘
                          │
                          ▼
             ┌──────────────────────────┐
             │  Split each book into     │
             │  chapters using regex     │
             │  (each book has its own   │
             │  chapter heading format)  │
             └────────────┬─────────────┘
                          │
                          ▼
             ┌──────────────────────────┐
             │  Chunk each chapter into  │
             │  ~1,800 char paragraphs   │
             │  (max 2,200 chars)        │
             │                          │
             │  Groups consecutive       │
             │  paragraphs together      │
             │  until the target size    │
             └────────────┬─────────────┘
                          │
                          ▼
             ┌──────────────────────────┐
             │  Generate a deterministic │
             │  UUID for each chunk      │
             │  (book#:chapter#:chunk#)  │
             │                          │
             │  This prevents duplicates │
             │  on re-ingestion!         │
             └────────────┬─────────────┘
                          │
                          ▼
        ┌─────────────────┴─────────────────┐
        │                                   │
        ▼                                   ▼
  ┌────────────────┐               ┌────────────────┐
  │  ChromaDB       │               │  SQLite FTS5    │
  │  (Vector Store) │               │  (BM25 Store)   │
  │                 │               │                 │
  │  Stores the     │               │  Stores the     │
  │  384D embedding │               │  raw text for   │
  │  + text +       │               │  keyword search │
  │  metadata       │               │  + metadata     │
  └─────────────────┘               └─────────────────┘
```

### What each chunk looks like after ingestion

| Field | Vector Store (ChromaDB) | BM25 Store (SQLite) |
|---|---|---|
| **ID** | `uuid5("hp1:ch3:chunk2")` | Same UUID |
| **Content** | The text passage | Same text |
| **Embedding** | 384-dimension vector | Not stored (not needed) |
| **Title** | `"Sorcerer's Stone — Ch.3: Letters from No One [2/5]"` | Same title |
| **Metadata** | `{source: "hp-books", book_number: 1, chapter_title: "...", ...}` | Same (as JSON) |
| **Permanent** | `"true"` | `1` |

> **Why two stores?** Because they're good at different things. Vector search understands *meaning*. BM25 finds *exact words*. Together, they cover each other's blind spots.

---


## Step 1 — The Query Arrives

A query can come from two places:

| Entry Point | What Happens |
|---|---|
| **Search endpoint** (`GET /api/search`) | Returns matching chunks directly |
| **Chat endpoint** (`POST /api/chat/{id}/message`) | Retrieves chunks, then feeds them to GPT-4o-mini for a conversational answer |

Both use the **same hybrid search** under the hood.

---


## Step 2 — Vector Search (Semantic Understanding)

```
"What happened to Dumbledore?"
              │
              ▼
┌──────────────────────────────────┐
│  Sentence Transformer            │
│  Model: all-MiniLM-L6-v2        │
│                                  │
│  Converts the query into a       │
│  384-dimensional number array    │
│  (an "embedding")                │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│  ChromaDB Cosine Similarity      │
│                                  │
│  Compares the query embedding    │
│  against every stored chunk      │
│  embedding                       │
│                                  │
│  Finds chunks whose MEANING      │
│  is closest to the query         │
└──────────────┬───────────────────┘
               │
               ▼
         Top-k results
    (ranked by similarity score)
```

**What it's great at:** Understanding intent. "What happened to Dumbledore?" will match passages about his death, the tower scene, and Snape — even if those passages don't contain the word "happened."

**Where it struggles:** Exact names, rare terms, or very specific phrasing.

---


## Step 3 — BM25 Search (Keyword Matching)

```
"What happened to Dumbledore?"
              │
              ▼
┌──────────────────────────────────┐
│  SQLite FTS5 Full-Text Search    │
│                                  │
│  Breaks query into tokens and    │
│  runs a MATCH query against      │
│  the FTS5 index                  │
│                                  │
│  Uses the BM25 ranking formula:  │
│  rewards term frequency,         │
│  penalizes common words          │
└──────────────┬───────────────────┘
               │
               ▼
         Top-k results
    (ranked by BM25 relevance)
```

**What it's great at:** Exact word matches. If "Dumbledore" appears in a chunk, BM25 *will* find it.

**Where it struggles:** Synonyms, paraphrasing, and understanding context. A passage about "the headmaster's fall" won't match unless it says "Dumbledore."

---


## Step 4 — Reciprocal Rank Fusion (The Merge)

This is where the magic happens. Both search methods return ranked lists. RRF merges them fairly without needing to normalize scores.

```
Vector Results              BM25 Results
(by meaning)                (by keywords)
┌──────────────┐            ┌──────────────┐
│ 1. Chunk A   │            │ 1. Chunk C   │
│ 2. Chunk B   │            │ 2. Chunk A   │   ← Chunk A appears
│ 3. Chunk C   │            │ 3. Chunk D   │     in BOTH lists!
│ 4. Chunk D   │            │ 4. Chunk E   │
│ 5. Chunk E   │            │ 5. Chunk B   │
└──────────────┘            └──────────────┘
        │                          │
        └────────────┬─────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │   RRF Score Formula     │
        │                        │
        │   For each chunk:       │
        │   score = 1/(60+rank₁)  │
        │        + 1/(60+rank₂)   │
        │                        │
        │   (60 is the standard   │
        │    smoothing constant)  │
        └────────────┬───────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │   Merged & Re-ranked    │
        │                        │
        │   1. Chunk A  ← winner │  Both lists liked it
        │   2. Chunk C           │
        │   3. Chunk B           │
        │   4. Chunk D           │
        │   5. Chunk E           │
        └────────────────────────┘
```

### Why RRF works well

- A chunk that appears in **both** lists gets a combined (higher) score
- A chunk ranked #1 in one list but absent from the other can still rank well, but won't dominate
- No need to compare or normalize raw scores from different systems — only **ranks** matter
- The constant `k=60` prevents top-ranked items from having outsized influence

---


## Step 5a — Search Response (Direct)

If the query came from the **search endpoint**, the merged results are returned directly:

```
GET /api/search?q=What+happened+to+Dumbledore&source=sample&mode=hybrid

Response:
{
  "results": [
    {
      "id": "chunk-uuid",
      "title": "Half-Blood Prince — Ch.27: The Lightning Struck Tower [1/2]",
      "content": "...the actual text passage...",
      "score": 0.032,
      "metadata": {
        "source": "hp-books",
        "book_number": 6,
        "chapter_title": "The Lightning Struck Tower"
      }
    },
    ...
  ]
}
```

The `mode` parameter lets you pick your search strategy:

| Mode | What runs |
|---|---|
| `hybrid` (default) | Vector + BM25 → RRF merge |
| `vector` | Vector search only |
| `bm25` | BM25 search only |

---


## Step 5b — Chat Response (With LLM)

If the query came from the **chat endpoint**, the chunks are fed to GPT-4o-mini as context:

```
┌─────────────────────────────────────────────────┐
│  Hybrid Search returns top 5 chunks             │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────┐
│  Build LangChain message list:                    │
│                                                  │
│  1. SystemMessage                                │
│     "You are a helpful assistant. Use the         │
│      provided context to answer. Be concise."    │
│                                                  │
│  2. Chat history (previous turns)                │
│     HumanMessage → AIMessage → HumanMessage...   │
│                                                  │
│  3. Retrieved context block                       │
│     [All 5 chunks formatted as reference text]   │
│                                                  │
│  4. Current HumanMessage                         │
│     "What happened to Dumbledore?"               │
└──────────────────────┬───────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────┐
│  LangChain ChatOpenAI.invoke(messages)            │
│  Model: gpt-4o-mini                              │
│                                                  │
│  The LLM reads the context + history and         │
│  generates a grounded, conversational answer     │
└──────────────────────┬───────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────┐
│  Response saved to chat history (SQLite)          │
│  Both the user message and AI response            │
│  are stored for multi-turn conversation          │
└──────────────────────────────────────────────────┘
```

> **LangChain's role is focused:** It provides the `ChatOpenAI` wrapper and message types (`SystemMessage`, `HumanMessage`, `AIMessage`). No chains, no LangChain retrievers — just a clean `.invoke()` call with a structured message list.

---


## The Tech Stack at a Glance

```
┌─────────────────────────────────────────────────────┐
│                    QUERY LAYER                       │
│                                                     │
│  FastAPI routes → hybrid_search_fn() → responses    │
├───────────────────────┬─────────────────────────────┤
│    SEMANTIC SEARCH    │      KEYWORD SEARCH          │
│                       │                             │
│  Sentence Transformers│   SQLite FTS5               │
│  all-MiniLM-L6-v2    │   BM25 ranking              │
│  (384D embeddings)    │   (built-in algorithm)      │
│         +             │         +                   │
│  ChromaDB             │   SQLite with triggers      │
│  (cosine similarity)  │   (auto-synced FTS index)   │
├───────────────────────┴─────────────────────────────┤
│                  MERGE LAYER                         │
│                                                     │
│  Reciprocal Rank Fusion (k=60)                      │
├─────────────────────────────────────────────────────┤
│                  CHAT LAYER (optional)               │
│                                                     │
│  LangChain ChatOpenAI → gpt-4o-mini                │
│  Chat history in SQLite                             │
├─────────────────────────────────────────────────────┤
│                  DATA LAYER                          │
│                                                     │
│  7 HP books → paragraph-aware chunking              │
│  ~1,800 chars/chunk → dual-stored in both DBs       │
│  Deterministic UUIDs → idempotent re-ingestion      │
└─────────────────────────────────────────────────────┘
```

---


## Key Config Values

| Setting | Value | Where |
|---|---|---|
| Embedding model | `all-MiniLM-L6-v2` | `config.py` |
| Embedding dimensions | 384 | Model default |
| LLM model | `gpt-4o-mini` | `config.py` |
| Target chunk size | 1,800 chars | `services/chunking.py` |
| Max chunk size | 2,200 chars | `services/chunking.py` |
| Min chunk size | 200 chars | `services/chunking.py` |
| Embedding batch size | 64 | `services/ingestion.py` |
| RRF constant (k) | 60 | `services/hybrid_search.py` |
| Default search limit | 10 | Router defaults |
| Max search limit | 100 | Router validation |
| Vector distance metric | Cosine | `services/vector_store.py` |
| Sample data tag | `"hp-books"` | `services/ingestion.py` |

---


## Why This Architecture?

| Decision | Reasoning |
|---|---|
| **Two search methods** | Vector catches meaning, BM25 catches exact terms — together they miss less |
| **RRF over weighted scores** | No need to tune weights or normalize scores — rank-based fusion is robust |
| **Paragraph-aware chunking** | Keeps logical paragraphs together instead of cutting mid-sentence |
| **Deterministic UUIDs** | App can restart safely without creating duplicate chunks |
| **Permanent flag on sample data** | Auto-cleanup (runs daily) only removes user uploads older than 30 days |
| **SQLite FTS5 triggers** | BM25 index stays in sync automatically — no manual index updates needed |
| **LangChain for chat only** | Lightweight — no heavy chain abstractions, just message formatting + LLM call |
