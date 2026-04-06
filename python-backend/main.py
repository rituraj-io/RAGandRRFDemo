"""
FastAPI application entry point.

Initializes all services, registers routers, and schedules
the daily cleanup background task.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from config import settings
from services.embedding import EmbeddingService
from services.vector_store import VectorStore
from services.bm25_store import BM25Store
from services.chat_store import ChatStore
from services.chat import ChatService
from services.cleanup import run_cleanup
from services.ingestion import ingest_hp_books
from services.hybrid_search import reciprocal_rank_fusion
from routers.documents import create_documents_router
from routers.search import create_search_router
from routers.chat import create_chat_router


# -- Logging --

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -- Service initialization --

embedding_service = EmbeddingService(model_name=settings.embedding_model)
vector_store = VectorStore(persist_path=settings.chroma_path, embedding_service=embedding_service)
bm25_store = BM25Store(db_path=settings.sqlite_bm25_path)
chat_store = ChatStore(db_path=settings.sqlite_chat_path)

chat_service = None
if settings.chat_enabled:
    chat_service = ChatService(api_key=settings.llm_api_key, model=settings.llm_model)
    logger.info("Chat enabled with model: %s", settings.llm_model)
else:
    logger.info("Chat disabled — no LLM_API_KEY in .env")


# -- Hybrid search helper --

def hybrid_search_fn(query: str, limit: int = 5, doc_id: str | None = None, source: str | None = None) -> list[dict]:
    """Run hybrid search across both stores, scoped by doc_id or source."""

    # Build filters
    vector_where = None
    bm25_doc_id = None
    bm25_source = None

    if doc_id:
        vector_where = {"doc_id": doc_id}
        bm25_doc_id = doc_id
    elif source == "sample":
        vector_where = {"source": "hp-books"}
        bm25_source = "hp-books"

    vector_results = vector_store.search(query, limit=limit, where=vector_where)
    bm25_results = bm25_store.search(query, limit=limit, doc_id=bm25_doc_id, source=bm25_source)
    return reciprocal_rank_fusion(vector_results, bm25_results, limit=limit)


# -- Background cleanup task --

async def cleanup_loop():
    """Run cleanup every 24 hours."""
    while True:
        await asyncio.sleep(86400)  # 24 hours
        try:
            result = run_cleanup(vector_store, bm25_store, chat_store, max_age_days=30)
            logger.info("Cleanup completed: %s", result)
        except Exception as e:
            logger.error("Cleanup failed: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle — start cleanup task."""
    logger.info("Starting RAG backend...")

    # Auto-ingest HP books on first startup
    ingest_hp_books(vector_store, bm25_store, embedding_service, settings.hp_books_path)

    task = asyncio.create_task(cleanup_loop())
    yield
    task.cancel()
    logger.info("Shutting down RAG backend.")


# -- App --

app = FastAPI(
    title="RAG Backend",
    description="Hybrid search RAG system with optional LLM chat.",
    version="0.1.0",
    lifespan=lifespan,
)


# -- Register routers --

app.include_router(create_documents_router(vector_store, bm25_store, embedding_service, chat_store))
app.include_router(create_search_router(vector_store, bm25_store))
app.include_router(create_chat_router(
    chat_store=chat_store,
    chat_service=chat_service,
    hybrid_search_fn=hybrid_search_fn,
    chat_enabled=settings.chat_enabled,
))


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "chat_enabled": settings.chat_enabled}
