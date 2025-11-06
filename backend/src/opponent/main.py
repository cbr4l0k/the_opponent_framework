"""FastAPI application entry point for The Opponent Framework."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .config import settings
from .api import notes as notes_api

# +----------------------------+
# |--- Application Lifespan ---|
# +----------------------------+

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown.
 
    Startup:
        - Ensure required directories exist
        - Initialize the NoMa note creator agent
 
    Shutdown:
        - Cleanup resources (if needed)
    """
    # Startup
    print("🚀 Starting Opponent Framework API...")
    settings.ensure_directories()

    notes_api.initialize_note_creator(ollama_model=settings.ollama_model)
    print(f"✅ NoMa creator initialized with model: {settings.ollama_model}")

    yield

    # Shutdown
    print("🛑 Shutting down Opponent Framework API...")

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
