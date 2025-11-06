"""Configuration management using pydantic-settings."""

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Settings can be provided via:
        - Environment variables
    - .env file in the backend directory
    - Direct instantiation (for testing)

    Example .env file:
        `OLLAMA_MODEL=llama3.1`
        `OBSIDIAN_VAULT_PATH=/path/to/vault`
        `OLLAMA_BASE_URL=http://localhost:11434`
    """
    model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore"  # Ignore extra fields in .env
            )
    log_level: str = Field(
            default="INFO",
            description="Logging level for the application."
            )

    # Ollama config
    ollama_model: str = Field(
            default="phi3:3.8b",
            description="Name of the Ollama model to use for LLM operations."
            )
    ollama_base_url: str = Field(
            default="http://localhost:11434",
            description="Base URL for the Ollama API."
            )

    # ChromaDB config
    chroma_persist_dir: str = Field(
            default="./data/chroma",
            description="Directory path for ChromaDB database."
            )
    chroma_collection: str = Field(
            default="obsidian_notes",
            description="Name of the ChromaDB collection to use."
            )
    embedding_model: str = Field(
            default="all-MiniLM-L6-v2",
            description="Model name for generating embeddings."
            )

    # Obsidian config
    vault_path: str = Field(
            default="./vault",
            description="Path to the Obsidian vault directory."
            )

    # API config
    api_host: str = Field(
            default="0.0.0.0",
            description="Host address for the API server."
            )
    api_port: int = Field(
            default=8000,
            description="Port number for the API server."
            )
    cors_origins: str = Field(
            default="http://localhost:5173",
            description="Comma-separated list of allowed CORS origins."
            )

    # RAG config
    top_k_results: int = Field(
            default=5,
            ge=1,
            le=50,
            description="Number of results to return from vector search."
            )
    chunk_size: int = Field(
            default=512,
            ge=100,
            le=2000,
            description="Size of text chunks for vectorization. The limit is between 100 and 2000 because, beyond that, the embedding model may not handle larger chunks effectively."
            )
    chunk_overlap: int = Field(
            default=50,
            ge=0,
            le=500,
            description="Overlap between chunks for better context."
            )

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        Path(self.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
        Path(self.vault_path).mkdir(parents=True, exist_ok=True)

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins string into list."""
        return [
                origin.strip() 
                for origin in self.cors_origins.split(",")
                ]

settings = Settings()
