"""ChromaDB vectorstore management for RAG operations."""

from pathlib import Path
from typing import Any
import chromadb
from chromadb.config import Settings as ChromaSettings
from numpy import where
from sentence_transformers import SentenceTransformer
import frontmatter

class VectorStore:
    """Manages ChromaDB vectorstore for Obsidian notes."""

    def __init__(self, 
                 persist_directory: str, 
                 collection_name: str,
                 embedding_model_name: str
                 ) -> None:
        """Initialize the ChromaDB vector store with SentenceTransformer embeddings.
        Args:
            `persist_directory` (str): Directory to persist the ChromaDB database.
            `collection_name` (str): Name of the collection to use/create.
            `embedding_model_name` (str): Name of the SentenceTransformer model to use for embeddings."""
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model_name

        # INit ChromaDB with persistence
        self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    )
                )

        # Load embedding model
        self.embedding_model = SentenceTransformer(self.embedding_model_name)

        # Get/Create collection :D
        self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}, # Cosine similarity for semantic search
                )

    def _parse_markdown(self, file_path: Path) -> dict[str, Any]:
        """Extract frontmatter and content from a markdown file."""
        with file_path.open("r", encoding="utf-8") as f:
            post = frontmatter.load(f)
        tags = post.get("tags", [])
        valid_tags = [tag for tag in tags if tag is not None] # type: ignore
        return {
                "content": post.content,
                "metadata": {
                    "path": str(file_path),
                    "title": post.get("title", file_path.stem),
                    "tags": ','.join(valid_tags)
                    },
                }

    def _chunk_document(
            self,
            content: str,
            chunk_size: int = 512,
            overlap: int = 50,
            ) -> list[str]:
        """Split document itno paragraph-level chunks —normally ideas are expressed in paragraphs—."""

        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

        chunks = []
        current_chunk = []
        current_length = 0

        for paragraph in paragraphs:
            paragraph_length = len(paragraph.split())

            # If adding this paragraph exceeds chunk size, finalize current chunk
            if current_length + paragraph_length > chunk_size and current_chunk:
                chunks.append("\n\n".join(current_chunk))
                # Keep last paragraph for overlap
                current_chunk = [current_chunk[-1]] if current_chunk else []
                current_length = len(current_chunk[0].split()) if current_chunk else 0

            current_chunk.append(paragraph)
            current_length += paragraph_length

        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        # I there was no split, it means content is only a single chunk
        return chunks if chunks else [content]

    def index_vault(self, vault_path: str) -> dict[str, int]:
        """
        Index all markdown files in the Obsidian vault.

        Args:
            `vault_path`: Path to Obsidian vault
        Returns:
            Statistics about indexed documents
        """
        vault = Path(vault_path)
        if not vault.exists() or not vault.is_dir():
            raise ValueError(f"Vault path {vault_path} does not exist or is not a directory.")
        
        # Let's search for the files in the directories
        markdown_files = list(vault.rglob("*.md"))

        if not markdown_files:
            return {"total_notes": 0, "total_chunks": 0}

        documents, metadatas, ids = [], [], []

        # Start indexing each file
        for file_path in markdown_files:
            try:
                note_data = self._parse_markdown(file_path)
                chunks = self._chunk_document(note_data["content"])
                for chunk_idx, chunk in enumerate(chunks):
                    doc_id = f"{file_path.stem}_{chunk_idx}"
                    ids.append(doc_id)
                    documents.append(chunk)
                    metadatas.append({
                        **note_data.get("metadata", {}),
                        'chunk_index': chunk_idx,
                        'total_chunks': len(chunks),
                    })

            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                continue

        if not documents:
            return {"total_notes": 0, "total_chunks": 0}

        embeddings = self.embedding_model.encode(
                documents,
                show_progress_bar=True,
                batch_size=32,	# This literally represents how many documents to process in parallel
                convert_to_numpy=True,
                ).tolist()

        # Add to vector database/collection
        self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings,
                )

        return {
                "total_notes": len(markdown_files),
                "total_chunks": len(documents),
                }


    def search(
            self,
            query: str,
            top_k: int = 5,
            filter_metadata: dict[str, Any] | None = None,
            ) -> list[dict[str, Any]]:
        """
        Search for similar documents in the vectorstore.

        Args:
            `query`: Search query text
            `top_k`: Number of results to return
            `filter_metadata`: Optional metadata filters (e.g., tags)
        Returns:
            List of matching documents with scores
        """
        query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)[0].tolist()

        # Prepare filter
        where_filter = filter_metadata if filter_metadata else None

        # Query ChromaDB
        query_args = { 
                      "query_embeddings": [query_embedding],
                      "n_results": top_k,
                      "include": ["documents", "metadatas", "distances"],
                      }
        if where_filter:
            query_args["where"] = where_filter
        results = self.collection.query( **query_args)

        # Handle missing or empty results safely
        if not results or not results.get("documents"):
            return []

        # Format results
        formatted_results = []
        for doc, meta, dist in zip(
                results.get("documents", [[]])[0], # type: ignore
                results.get("metadatas", [[]])[0], # type: ignore
                results.get("distances", [[]])[0], # type: ignore
                ):
            formatted_results.append({
                "content": doc,
                "metadata": meta,
                "similarity_score": 1 - dist,  # Convert distance to similarity
                })

        return formatted_results


    def get_by_path(self, note_path: str) -> dict[str, Any] | None:
        """
        Retrieve a specific note by its file path.

        Args:
            `note_path`: Path to the note file
        Returns:
            Note data or None if not found
        """
        results = self.collection.get(
                where={"path": note_path},
                include=["documents", "metadatas"],
                )
        if not results["documents"]:
            return None

        return {
                "documents": '\n\n'.join(results["documents"]),
                "metadatas": results["metadatas"][0],			# type: ignore
                }

    def update_document(self, note_path: str, content: str) -> None:
        """
        Update a document in the vectorstore.
        TODO: Implement document update/re-indexing
        Args:
            `note_path`: Path to the note file
            `content`: Updated note content
        """
        old_docs = self.collection.get(
                where={"path": note_path},
                )

        if old_docs["ids"]:
            self.collection.delete(ids=old_docs["ids"])

        file_path = Path(note_path)
        note_data = self._parse_markdown(file_path)
        chunks = self._chunk_document(content)

        documents, metadatas, ids = [], [], []
        for chunk_idx, chunk in enumerate(chunks):
            doc_id = f"{file_path.stem}_{chunk_idx}"
            ids.append(doc_id)
            documents.append(chunk)
            metadatas.append({
                    **note_data.get("metadata", {}),
                    'chunk_index': chunk_idx,
                    'total_chunks': len(chunks),
                    })

        embeddings = self.embedding_model.encode(documents, convert_to_numpy=True).tolist()

        self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings,
                )









