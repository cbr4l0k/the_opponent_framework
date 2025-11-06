"""FastAPI application entry point for The Opponent Framework."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .api import links as links_api
from .api import notes as notes_api
from .config import settings
from .rag import Retriever, VectorStore

logger = logging.getLogger("uvicorn.error")

# +----------------------------+
# |--- Application Lifespan ---|
# +----------------------------+

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown.
 
    Startup:
        - Ensure required directories exist
        - Initialize RAG components (VectorStore, Retriever)
        - Initialize all agents (NoMa, Linker)
 
    Shutdown:
        - Cleanup resources (if needed)
    """
    # Startup
    logger.info("🚀 Starting Opponent Framework API...")
    settings.ensure_directories()
 
    # Initialize RAG components
    logger.info("📚 Initializing RAG components...")
    vectorstore = VectorStore(
        persist_directory=settings.chroma_persist_dir,
        collection_name=settings.chroma_collection,
        embedding_model_name=settings.embedding_model
    )
    logger.info(f"✅ VectorStore initialized: {settings.chroma_collection}")
 
    retriever = Retriever(
        vectorstore=vectorstore,
        ollama_model=settings.ollama_model,
        top_k=settings.top_k_results
    )
    logger.info(f"✅ Retriever initialized with top_k={settings.top_k_results}")
 
    # Initialize agents
    logger.info("🤖 Initializing agents...")
    notes_api.initialize_note_creator(ollama_model=settings.ollama_model)
    logger.info(f"✅ NoMa creator initialized")
 
    links_api.initialize_note_linker(retriever=retriever, max_links=settings.top_k_results)
    logger.info(f"✅ Note linker initialized")
 
    logger.info(f"✅ All systems ready! Model: {settings.ollama_model}")
    logger.info(f"📖 API docs: http://{settings.api_host}:{settings.api_port}/docs")

    yield

    # Shutdown
    logger.info("🛑 Shutting down Opponent Framework API...")

# +---------------------------+
# |--- FastAPI Application ---|
# +---------------------------+

app = FastAPI(
        title="Opponent Framework API",
        description=(
            "A three-stage AI-powered system for creating structured notes, "
            "linking them intelligently, and challenging your arguments."
            ),
        version="0.1.0",
        lifespan=lifespan
        )

# +-----------------------+
# |--- CORS Middleware ---|
# +-----------------------+

app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        )

# +-----------------------+
# |--- include routers ---|
# +-----------------------+

app.include_router(notes_api.router)

# +-----------------------+
# |--- Endpoints setup ---|
# +-----------------------+

@app.get("/")
async def root():
    """
    Root endpoint with API information.
 
    Returns:
        Welcome message and available endpoints
    """
    return {
        "message": "Welcome to the Opponent Framework API",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": {
            "notes": "/api/notes",
            "health": "/api/notes/health"
        }
    }
 
 
@app.get("/health")
async def health():
    """
    Global health check endpoint.
 
    Returns:
        Overall API health status
    """
    return {
        "status": "healthy",
        "message": "Opponent Framework API is running",
        "configuration": {
            "ollama_model": settings.ollama_model,
            "vault_path": settings.vault_path,
        }
    }

# +---------------+
# |--- App Run ---|
# +---------------+

def main() -> None:
    """CLI entry point for running the server."""

    uvicorn.run(
        "opponent.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
