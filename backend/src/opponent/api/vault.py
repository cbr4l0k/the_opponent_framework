"""API endpoints for vault management."""
 
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
 
from ..rag import VectorStore
 
 
# +-------------------------------------+
# |--- Requests/Response Data Models ---|
# +-------------------------------------+
 

class IndexVaultRequest(BaseModel):
    """Request model for indexing a vault."""
 
    vault_path: str = Field(
        ...,
        description="Path to the vault directory to index",
        examples=[
            "./vault"
            ]
    )
 
class IndexVaultResponse(BaseModel):
    """Response model for vault indexing."""
 
    total_notes: int = Field(..., description="Total number of notes indexed")
    total_chunks: int = Field(..., description="Total number of chunks created")
    vault_path: str = Field(..., description="Path that was indexed")
 
 
# |--------------------|
# |--- Router Setup ---|
# |--------------------|

 
router = APIRouter(prefix="/api/vault", tags=["vault"])
 
# Global vectorstore instance (set in main.py)
vectorstore: VectorStore | None = None
 
def initialize_vectorstore(vs: VectorStore):
    """Set the global vectorstore instance."""
    global vectorstore
    vectorstore = vs
 
 
# |-----------------|
# |--- Endpoints ---|
# |-----------------|
 

@router.post("/index", response_model=IndexVaultResponse)
async def index_vault(request: IndexVaultRequest):
    """
    Index a vault directory into the vectorstore.
 
    This will:
    1. Scan the vault for all .md files
    2. Parse frontmatter and content
    3. Create embeddings
    4. Store in ChromaDB
 
    Args:
        `request`: Path to the vault to index
    Returns:
        IndexVaultResponse with statistics
    Raises:
        `HTTPException`: If indexing fails
    """
    if vectorstore is None:
        raise HTTPException(
            status_code=500,
            detail="VectorStore not initialized. Check server configuration."
        )
 
    try:
        # Index the vault
        stats = vectorstore.index_vault(request.vault_path)
 
        return IndexVaultResponse(
            total_notes=stats["total_notes"],
            total_chunks=stats["total_chunks"],
            vault_path=request.vault_path
        )
 
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to index vault: {str(e)}"
        )
 
 
@router.get("/health")
async def health_check():
    """Check if the vault service is healthy."""
    if vectorstore is None:
        return {
            "status": "unhealthy",
            "message": "VectorStore not initialized"
        }
 
    return {
        "status": "healthy",
        "message": "Vault service is ready"
    }
