"""API endpoints for note creation using the Noma method."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from ..agents import NomaNoteCreator


# +-------------------------------------+
# |--- Requests/Response Data Models ---|
# +-------------------------------------+


class NoMaRequests(BaseModel):
    """Request model for creating a note using the NoMa method."""
    interesting: str = Field(
            ...,
            description="What topic do you find interesting.",
            min_length=10,
            examples=[
                "I find it fascinating how...",
                ]
            )
    reminds_me: str = Field(
            ...,
            description="What this reminds you of.",
            min_length=10,
            examples=[
                "This reminds me of...",
                ]
            )
    similar_because: str = Field(
            ...,
            description="Why is this similar to the initial interest.",
            min_length=10,
            examples=[
                "It's similar because...",
                ]
            )
    different_because: str = Field(
            ...,
            description="Why this is different from something else",
            min_length=10,
            examples=[
                "It's different because...",
                ]
            )
    important_because: str = Field(
            ...,
            description="Why is this important to you.",
            min_length=10,
            examples=[
                "It's important because...",
                ]
            )
    has_internet: bool = Field(
            default=False,
            description="Whether to fetch external resources from the internet. Currently is not correctly implemented 😿, so keep it `False`.",
            )

class NoMaResponse(BaseModel):
    """Response model for a created note."""
 
    title: str = Field(..., description="Generated title for the note")
    tags: list[str] = Field(..., description="Topic tags for the note")
    content: str = Field(..., description="The synthesized note content")
    resources: Optional[list[dict]] = Field(None, description="External resources (if has_internet=True)")
    markdown: str = Field(..., description="Complete markdown with frontmatter")
    filename: str = Field(..., description="Suggested filename for the note")

class HealthResponse(BaseModel):
    """Health check response."""
 
    status: str = Field(..., description="Service status")
    message: str = Field(..., description="Status message")


# |--------------------|
# |--- Router Setup ---|
# |--------------------|


router = APIRouter(prefix="/api/notes", tags=["notes"])

# Global agent instance (initialized in main.py)
noma_creator: Optional[NomaNoteCreator] = None

def initialize_note_creator(ollama_model: str):
    """
    Initialize the NoMa note creator agent.
 
    Args:
        `ollama_model`: Name of the Ollama model to use
    Note:
        This should be called once during app startup from main.py
    """
    global noma_creator
    noma_creator = NomaNoteCreator( ollama_model=ollama_model)


# |-----------------|
# |--- Endpoints ---|
# |-----------------|


@router.post("/create", response_model=NoMaResponse)
async def create_note(request: NoMaRequests) -> NoMaResponse:
    """Create a structured note using the NoMa method.
 
    The NoMa method transforms your 5 reflections into a coherent note:
    1. What's interesting
    2. What it reminds you of
    3. Why it's similar
    4. Why it's different
    5. Why it's important
 
    Args:
        `request`: NoMa reflections and configuration
    Returns:
        NoMaResponse with the generated note, title, tags, and markdown
    Raises:
        `HTTPException`: If note creation fails or agent not initialized
    """
    if noma_creator is None:
        raise HTTPException(
            status_code=500,
            detail="Note creator not initialized. Check server configuration."
        )
    try:
        # Parse request into state dict
        state = {
            "interesting": request.interesting,
            "reminds_me": request.reminds_me,
            "similar_because": request.similar_because,
            "different_because": request.different_because,
            "important_because": request.important_because,
            "has_internet": request.has_internet,
        }

        # Run the NoMa workflow
        result = await noma_creator.app.ainvoke(state)

        # Parse result into response model
        response = NoMaResponse(
            title=result["note_title"],
            tags=result["topic_tags"] or [],
            content=result["synthesized_note"],
            resources=result.get("resources"),
            markdown=result["final_output"],
            filename=result["output_file_name"],
        )

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating note: {str(e)}"
        )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check if the note creation service is healthy.
 
    Returns:
        HealthResponse with service status
    """
    if noma_creator is None:
        return HealthResponse(
            status="unhealthy",
            message="Note creator not initialized"
        )
 
    return HealthResponse(
        status="healthy",
        message="Note creation service is ready"
    )
