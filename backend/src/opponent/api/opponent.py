"""API endpoints for the adversarial opponent agent."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..agents import OpponentAgent
from ..rag import Retriever


# +-------------------------------------+
# |--- Requests/Response Data Models ---|
# +-------------------------------------+


class OpponentRequest(BaseModel):
    """Request model for challenging a claim with the opponent."""

    note_content: str = Field(
        ...,
        description="The note or claim to challenge",
        min_length=10
    )
    note_path: str | None = Field(
        default=None,
        description="Optional path to exclude from counter-evidence"
    )
    context: str | None = Field(
        default=None,
        description="Additional context about the claim"
    )
    max_evidence: int | None = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum pieces of counter-evidence to use"
    )


class CounterEvidence(BaseModel):
    """A piece of counter-evidence from the knowledge base."""

    content: str = Field(..., description="The counter-evidence text")
    source: str = Field(..., description="Source note title")
    path: str = Field(..., description="Path to the source note")
    score: float = Field(..., description="Relevance score")


class OpponentResponse(BaseModel):
    """Response model from the opponent."""

    summary: str = Field(..., description="Concise summary of opposition (2-3 sentences)")
    detailed_analysis: str = Field(..., description="Detailed challenge to the arguments")
    counter_evidence: list[CounterEvidence] = Field(..., description="Sources used for opposition")
    evidence_count: int = Field(..., description="Number of counter-evidence pieces found")


# |--------------------|
# |--- Router Setup ---|
# |--------------------|


router = APIRouter(prefix="/api/opponent", tags=["opponent"])

# Global instances (initialized in main.py)
opponent_agent: OpponentAgent | None = None


def initialize_opponent(retriever: Retriever, ollama_model: str, max_evidence: int = 5):
    """
    Initialize the opponent agent.

    Args:
        `retriever`: Retriever instance for finding counter-evidence
        `ollama_model`: Name of the Ollama model to use
        `max_evidence`: Default maximum pieces of counter-evidence
    Note:
        This should be called once during app startup from main.py
    """
    global opponent_agent
    opponent_agent = OpponentAgent(
        retriever=retriever,
        ollama_model=ollama_model,
        max_evidence=max_evidence
    )


# |-----------------|
# |--- Endpoints ---|
# |-----------------|


@router.post("/challenge", response_model=OpponentResponse)
async def challenge_claim(request: OpponentRequest):
    """
    Challenge a claim or note with evidence-based opposition.

    The opponent agent:
    1. Retrieves counter-evidence from your knowledge base
    2. Analyzes the claim for weaknesses and gaps
    3. Provides systematic challenges using only evidence (no opinions)

    Args:
        `request`: The claim to challenge and configuration
    Returns:
        OpponentResponse with detailed analysis and counter-evidence
    Raises:
        `HTTPException`: If challenge fails or agent not initialized
    """
    if opponent_agent is None:
        raise HTTPException(
            status_code=500,
            detail="Opponent agent not initialized. Check server configuration."
        )

    try:
        # Run the opponent workflow
        result = await opponent_agent.run(
            note_content=request.note_content,
            note_path=request.note_path,
            context=request.context,
            max_evidence=request.max_evidence
        )

        # Format counter-evidence
        counter_evidence = [
            CounterEvidence(
                content=evidence["content"],
                source=evidence["source"],
                path=evidence["path"],
                score=evidence["score"]
            )
            for evidence in (result["counter_evidence"] or [])
        ]

        # Build response
        response = OpponentResponse(
            summary=result["summary"] or "No opposition available.",
            detailed_analysis=result["detailed_analysis"] or "No analysis available.",
            counter_evidence=counter_evidence,
            evidence_count=len(counter_evidence)
        )

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to challenge claim: {str(e)}"
        ) from e


@router.get("/health")
async def health_check():
    """
    Check if the opponent service is healthy.

    Returns:
        Health status and configuration
    """
    if opponent_agent is None:
        return {
            "status": "unhealthy",
            "message": "Opponent agent not initialized"
        }

    return {
        "status": "healthy",
        "message": "Opponent service is ready",
        "max_evidence": opponent_agent.max_evidence,
        "model": opponent_agent.ollama_model
    }

