"""LangGraph agent for adversarial argument opposition."""

from typing import Optional, TypedDict
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from ..rag import Retriever
from ..prompts import OPPONENT_PROMPTS

MAX_CHARS_ANALYSIS = 500

class OpponentState(TypedDict):
    """# State for the opponent workflow.

    ## Input
    `note_content`: str  # The note/claim to challenge
    `note_path`: Optional[str]  # Path to exclude from counter-evidence (optional)
    `context`: Optional[str]  # Additional context about the claim (optional)
 
    ## Processing
    `max_evidence`: int  # Maximum pieces of counter-evidence to use (default: 5)
 
    ## Output
    `counter_evidence`: Optional[list[dict]]  # List of opposing arguments from vault
    `detailed_analysis`: Optional[str]  # Detailed challenge to the arguments
    `summary`: Optional[str]  # Concise summary of opposition
    """
    note_content: str
    note_path: Optional[str]
    context: Optional[str]
    max_evidence: int
    counter_evidence: Optional[list[dict]]
    detailed_analysis: Optional[str]
    summary: Optional[str]



class OpponentAgent:
    """Agent for challenging arguments using evidence-based opposition.

    - For now, it only works by using my own knowledge base via RAG. 
		TODO: Integrate internet search for broader perspectives.
    """

    def __init__(self, retriever: Retriever, ollama_model: str, max_evidence: int = 5) -> None:
        """
        Initialize the opponent agent.

        Args:
            vectorstore: ChromaDB vectorstore for RAG
            ollama_model: Name of the Ollama model to use
        """
        self.retriever = retriever
        self.ollama_model = ollama_model
        self.max_evidence = max_evidence
        self.llm = ChatOllama(model=ollama_model, temperature=0.3) # Lower temp for analytical work

        self.graph = StateGraph(OpponentState)

        # Add nodes
        self.graph.add_node("validate_input", self.validate_input)
        self.graph.add_node("retrieve_counter_evidence", self.retrieve_counter_evidence)
        self.graph.add_node("analyze_arguments", self.analyze_arguments)
        self.graph.add_node("summarize_opposition", self.summarize_opposition)

        # Add edges
        self.graph.set_entry_point("validate_input")
        self.graph.add_edge("validate_input", "retrieve_counter_evidence")
        self.graph.add_edge("retrieve_counter_evidence", "analyze_arguments")
        self.graph.add_edge("analyze_arguments", "summarize_opposition")
        self.graph.add_edge("summarize_opposition", END)

        # Compile
        self.app = self.graph.compile()

    async def validate_input(self, state: OpponentState) -> OpponentState:
        """`Node`: Validate that required inputs are provided."""
        if not state.get("note_content"):
            raise ValueError("Missing required input: note_content")

        if not state.get("max_evidence"):
            state["max_evidence"] = self.max_evidence

        return state

    async def retrieve_counter_evidence(self, state: OpponentState) -> OpponentState:
        """`Node`: Retrieve evidence that opposes or challenges the claim."""
 
        # Use the retriever's opposition-focused method
        results = await self.retriever.retrieve_for_opposition(
            claim=state["note_content"],
            context=state.get("context")
        )
 
        # Format 
        counter_evidence = []
        for result in results[:state["max_evidence"]]:
            metadata = result.get("metadata", {})
            counter_evidence.append({
                "content": result.get("content", ""),
                "source": metadata.get("title", "Unknown"),
                "path": metadata.get("path", ""),
                "score": result.get("rerank_score", result.get("score", 0.0))
            })
 
        state["counter_evidence"] = counter_evidence
        return state

    async def analyze_arguments(self, state: OpponentState) -> OpponentState:
        """`Node`: Analyze the claim and provide evidence-based challenges."""

        counter_evidence_text = ""
        for idx, evidence in enumerate(state.get("counter_evidence", []), start=1):
            counter_evidence_text += f"\n[Source {idx}: {evidence.get('source', 'Missing Source')}]\n"
            counter_evidence_text += f"{evidence['content']}\n"

        if not counter_evidence_text:
            state["detailed_analysis"] = (
                "No counter-evidence found in your knowledge base. "
                "The claim may be novel, or your vault lacks opposing perspectives."
            )
            return state
        prompt = OPPONENT_PROMPTS["analysis"].format(
                note_content=state["note_content"],
                counter_evidence=counter_evidence_text,
                )
        response = await self.llm.ainvoke(prompt)
        state["detailed_analysis"] = response.content

        return state

    async def summarize_opposition(self, state: OpponentState) -> OpponentState:
        """`Node`: Create a concise summary of the opposition."""
        if not state.get("detailed_analysis"):
            state["summary"] = "No analysis available"
            return state

        # Summary generation
        prompt = OPPONENT_PROMPTS["summary"].format(
            note_content=state["note_content"][:MAX_CHARS_ANALYSIS],  # First 500 chars
            detailed_analysis=state["detailed_analysis"]
        )
        response = await self.llm.ainvoke(prompt)
        state["summary"] = response.content 
        return state

    async def run(
        self,
        note_content: str,
        note_path: str | None = None,
        context: str | None = None,
        max_evidence: int | None = None
    ) -> OpponentState:
        """Run the opponent workflow to challenge a claim.
 
        Args:
            `note_content`: The note or claim to challenge
            `note_path`: Optional path to the note (for excluding from results)
            `context`: Optional additional context
            `max_evidence`: Optional override for max counter-evidence
        Returns:
            Final state with detailed analysis and summary
        """

        initial_state: OpponentState = {
            "note_content": note_content,
            "note_path": note_path,
            "context": context,
            "max_evidence": max_evidence or self.max_evidence,
            "counter_evidence": None,
            "detailed_analysis": None,
            "summary": None,
        }

        result = await self.app.ainvoke(initial_state)

        return result # type: ignore
