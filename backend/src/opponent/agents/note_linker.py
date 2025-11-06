"""LangGraph agent for finding and creating links between notes."""

from typing import Optional, TypedDict
from langgraph.graph import StateGraph, END
from ..rag.retrieval import Retriever

MAX_CHARS_REASON = 200

class NoteLinkState(TypedDict):
    """# State for the note linking workflow.
 
    ## Input
    `note_path`: str  # Path to the note file
    `note_content`: str  # Content of the note to find links for
 
    ## Processing
    `max_links`: int  # Maximum number of links to suggest (default: 5)
 
    ## Output
    `suggested_links`: Optional[list[dict]]  # List of {path, title, reason, score} dicts
    `link_summary`: Optional[str]  # Human-readable summary of suggestions
    """
    note_path: str
    note_content: str
    max_links: int
    suggested_links: Optional[list[dict]]
    link_summary: Optional[str]


class NoteLinker:
    """Agent for discovering semantic connections between notes."""

    def __init__(self, retriever: Retriever, max_links: int = 5) -> None:
        """
        Initialize the note linker agent.

        Args:
            `retriever`: Retriever instance for finding related notes
            `max_links`: Maximum number of links to suggest (default: 5)
        """
        self.retriever = retriever
        self.max_links = max_links

        self.graph = StateGraph(NoteLinkState)

        # Add nodes
        self.graph.add_node("validate_input", self.validate_input)
        self.graph.add_node("find_links", self.find_links)
        self.graph.add_node("format_suggestions", self.format_suggestions)

        # Add edges
        self.graph.set_entry_point("validate_input")
        self.graph.add_edge("validate_input", "find_links")
        self.graph.add_edge("find_links", "format_suggestions")
        self.graph.add_edge("format_suggestions", END)

        # Compile
        self.app = self.graph.compile()


    async def validate_input(self, state: NoteLinkState) -> NoteLinkState:
        """`Node`: Validate that required inputs are provided."""
        if not state.get("note_path"):
            raise ValueError("Missing required field: note_path")
 
        if not state.get("note_content"):
            raise ValueError("Missing required field: note_content")
 
        # Set default max_links if not provided
        if not state.get("max_links"):
            state["max_links"] = self.max_links
 
        return state

    async def find_links( self, state: NoteLinkState) -> NoteLinkState:
        """`Node`: Use retriever to find notes related to this one."""
        results = await self.retriever.retrieve_for_linking(
                note_content=state.get("note_content"),
                exclude_path=state.get("note_path"),
                )

        # Formatting 
        suggested_links = []
        for result in results[: state.get("max_links")]:
            metadata = result.get("metadata", {})
            suggested_links.append({
                "path": metadata.get("path", ""),
                "title": metadata.get("title", "Untitled"),
                "reason": result.get("snippet", "")[:MAX_CHARS_REASON],
                "score": result.get("score", 0.0),
            })
        
        state["suggested_links"] = suggested_links
        return state

    async def format_suggestions(self, state: NoteLinkState) -> NoteLinkState:
        """`Node`: Format link suggestions into a human-readable summary."""
        link = state.get("suggested_links", [])

        if not link:
            state["link_summary"] = "No related notes found for linking."
            return state

        summary_lines = [
                f"Found {len(link)} related note(s) for linking:",
                ]
        for idx, link in enumerate(link, start=1):
            title = link.get("title")
            path = link.get("path")
            score = link.get("score")

            summary_lines.append(f"{idx}. [[{title}]]")
            summary_lines.append(f"\t- Path: {path}")
            summary_lines.append(f"\t- Relevance: {score:.4f}")
            summary_lines.append("")

        state["link_summary"] = "\n".join(summary_lines).strip()
        return state

    async def run(self, note_path: str, note_content: str, max_links: int | None = None) -> NoteLinkState:
        """
        Run the note linking workflow.
 
        Args:
            `note_path`: Path to the note file
            `note_content`: Content of the note
            `max_links`: Optional override for max links to suggest
        Returns:
            Final state with suggested links and summary
        """
        initial_state: NoteLinkState = {
                "note_path": note_path,
                "note_content": note_content,
                "max_links": max_links or self.max_links,
                "suggested_links": None,
                "link_summary": None,
                }
        result = await self.app.ainvoke(initial_state)

        return result # type: ignore
