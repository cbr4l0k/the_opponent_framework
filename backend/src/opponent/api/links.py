"""API endpoints for note linking using RAG."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from ..agents import NoteLinker
from ..rag import Retriever


# +-------------------------------------+
# |--- Requests/Response Data Models ---|
# +-------------------------------------+


class LinkRequest(BaseModel):
    """Request model for finding related notes to link."""
 
    note_path: str = Field(
        ...,
        description="Path to the note file",
        examples=[
            "vault/my_note.md"
            ]
    )
    note_content: str = Field(
        ...,
        description="Content of the note to find links for",
        min_length=10
    )
    max_links: Optional[int] = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of links to suggest"
    )
 
 
class SuggestedLink(BaseModel):
    """A single suggested link to another note."""
 
    path: str = Field(..., description="Path to the related note")
    title: str = Field(..., description="Title of the related note")
    reason: str = Field(..., description="Why this note is relevant (preview)")
    score: float = Field(..., description="Relevance score (0.0 to 1.0)")
 
 
class LinkResponse(BaseModel):
    """Response model for link suggestions."""
 
    note_path: str = Field(..., description="Original note path")
    suggested_links: list[SuggestedLink] = Field(..., description="List of suggested links")
    summary: str = Field(..., description="Human-readable summary of suggestions")
    count: int = Field(..., description="Number of links found")
 


# |--------------------|
# |--- Router Setup ---|
# |--------------------|


router = APIRouter(prefix="/api/links", tags=["links"])
 
# Global instances (initialized in main.py)
note_linker: Optional[NoteLinker] = None
 
def initialize_note_linker(retriever: Retriever, max_links: int = 5):
    """
    Initialize the note linker agent.
 
    Args:
        retriever: Retriever instance for finding related notes
        max_links: Default maximum number of links to suggest
 
    Note:
        This should be called once during app startup from main.py
    """
    global note_linker
    note_linker = NoteLinker(
        retriever=retriever,
        max_links=max_links
    )


# |-----------------|
# |--- Endpoints ---|
# |-----------------|


@router.post("/find", response_model=LinkResponse)
async def find_links(request: LinkRequest) -> LinkResponse:
    """
    Find related notes to link to the provided note.
 
    Uses RAG (Retrieval-Augmented Generation) to find semantically similar notes in your vault based on the note's content.
 
    Args:
        `request`: Note path, content, and linking preferences
    Returns:
        LinkResponse with suggested links and relevance scores
    Raises:
        `HTTPException`: If linking fails or agent not initialized
    """
    if note_linker is None:
        raise HTTPException(
            status_code=500,
            detail="Note linker not initialized. Check server configuration."
        )
 
    try:
        # Run the note linking workflow
        result = await note_linker.run(
            note_path=request.note_path,
            note_content=request.note_content,
            max_links=request.max_links
        )
 
        # Parse request into state dict
        suggested_links = [
            SuggestedLink(
                path=link["path"],
                title=link["title"],
                reason=link["reason"],
                score=link["score"]
            )
            for link in (result["suggested_links"] or [])
        ]
 
        # Parse result into response model
        response = LinkResponse(
            note_path=request.note_path,
            suggested_links=suggested_links,
            summary=result["link_summary"] or "No links found.",
            count=len(suggested_links)
        )
 
        return response
 
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to find links: {str(e)}"
        )
 
 
@router.get("/health")
async def health_check():
    """
    Check if the note linking service is healthy.
 
    Returns:
        Health status and configuration
    """
    if note_linker is None:
        return {
            "status": "unhealthy",
            "message": "Note linker not initialized"
        }
 
    return {
        "status": "healthy",
        "message": "Note linking service is ready",
        "max_links": note_linker.max_links
    }
