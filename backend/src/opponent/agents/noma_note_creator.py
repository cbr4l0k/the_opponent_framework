"""LangGraph agent for creating notes using the Noma method."""

from typing import Any, Literal, Optional, TypedDict
from langgraph.graph import StateGraph, END
from ..prompts.noma_prompts import NOMA_PROMPTS
from ..structs.note import Resource, NoMaNote, NoteTags, NoteTitle
from ..misc.markdown_tools import MDBuilder
from langchain_ollama import ChatOllama


class NoMaState(TypedDict):
    """# State for the NoMa note-making workflow.

    ## Input: User's responses to the 5 prompts
    `interesting`: str  # "That's interesting" response
    `reminds_me`: str  # "That reminds me" response
    `similar_because`: str  # "It's similar because" response
    `different_because`: str  # "It's different because" response
    `important_because`: str  # "It's important because" response

    ## Processing flags
    `has_internet`: bool  # Whether internet access is available

    ## Output: Generated content
    `synthesized_note`: Optional[str]  # The coherent note
    `note_title`: Optional[str]  # The generated title
    `topic_tags`: Optional[list[str]]  # Topic tags (without #t/ prefix)
    `resources`: Optional[list[dict]]  # List of {title, url, reason} dicts
    `final_output`: Optional[str]  # The formatted final output
    `output_file_name`: Optional[str]  # Suggested file name for the note
    """
    interesting: str  
    reminds_me: str  
    similar_because: str  
    different_because: str  
    important_because: str  
    has_internet: bool  
    synthesized_note: Optional[str]  
    note_title: Optional[str]  
    topic_tags: Optional[list[str]]  
    resources: Optional[list[dict]]  
    final_output: Optional[str]  
    output_file_name: Optional[str]


class NomaNoteCreator:
    """Agent for creating structured notes using the Noma method."""

    def __init__(self, ollama_model: str, prompts: dict[str, str]) -> None:
        """
        Initialize the Noma note creator agent.

        Args:
            `ollama_model`: Name of the Ollama model to use
            `prompts`: Dictionary of Noma method prompts
        """
        self.ollama_model = ollama_model
        self.prompts = prompts
        self.llm =  ChatOllama(model=self.ollama_model, temperature=0.7)

        self.graph = StateGraph(NoMaState)

        # Adding nodes:
        self.graph.add_node("validate_responses", self.validate_responses)
        self.graph.add_node("generate_note", self.generate_note)
        self.graph.add_node("generate_title", self.generate_title)
        self.graph.add_node("generate_topic_tags", self.generate_topic_tags)
        self.graph.add_node("merge_metadata", self.merge_metadata)
        self.graph.add_node("fetch_resources", self.fetch_resources)
        self.graph.add_node("format_output", self.format_final_output)

        # Adding edges:
        self.graph.set_entry_point("validate_responses")
        self.graph.add_edge("validate_responses", "generate_note")

        # Parallel execution:
        self.graph.add_edge("generate_note", "generate_title")
        self.graph.add_edge("generate_note", "generate_topic_tags")

        # Converging edges:
        self.graph.add_edge("generate_title", "merge_metadata")
        self.graph.add_edge("generate_topic_tags", "merge_metadata")

        # Conditional edge to fetch resources:
        self.graph.add_conditional_edges(
                "merge_metadata",
                self.should_fetch_resources,
                {
                    "fetch_resources": "fetch_resources",
                    "format_output": "format_output"
                    }
                )
        self.graph.add_edge("fetch_resources", "format_output")
        self.graph.add_edge("format_output", END)

        # Compile
        self.app = self.graph.compile()


    async def validate_responses(self, state: NoMaState) -> NoMaState:
        """ `Node`: Validate that all 5 NoMa responses are provided."""

        required_fields = [ "interesting", "reminds_me", "similar_because", "different_because", "important_because"]

        for field in required_fields:
            if not state.get(field):
                raise ValueError(f"Missing required NoMa response: {field}")

        return state

    async def generate_note(self, state: NoMaState) -> NoMaState:
        """`Node`: Generate a structured note using the Noma method."""
        prompt = NOMA_PROMPTS['synthesis'].format(
                interesting=state["interesting"],
                reminds_me=state["reminds_me"],
                similar_because=state["similar_because"],
                different_because=state["different_because"],
                important_because=state["important_because"]
                )
        structured_model = self.llm.with_structured_output(NoMaNote)
        note = await structured_model.ainvoke(prompt)
        
        return {"synthesized_note": note.content} # type: ignore

    async def generate_title(self, state:NoMaState) -> NoMaState:
        """`Node`: Generate a title for the synthesized note."""
        prompt = NOMA_PROMPTS['title'].format(
                note=state["synthesized_note"]
                )
        structured_model = self.llm.with_structured_output(NoteTitle)

        title = await structured_model.ainvoke(prompt)

        return {"note_title": title.title} # type: ignore

    async def generate_topic_tags(self, state:NoMaState) -> NoMaState:
        """`Node`: Generate topic tags for the synthesized note."""
        prompt = NOMA_PROMPTS['tags'].format(
                note=state["synthesized_note"]
                )
        structured_model = self.llm.with_structured_output(NoteTags)
        tags = await structured_model.ainvoke(prompt)

        return {
                "topic_tags": [f"{tag.lstrip('#t/')}" for tag in tags.tags]
                } # type: ignore

    async def fetch_resources(self, state:NoMaState) -> NoMaState:
        """`Node`: Fetch relevant resources for the synthesized note."""
        if not state.get("has_internet"):
            state["resources"] = None
            return state

        note = state["synthesized_note"]
        prompt = NOMA_PROMPTS['resources'].format(
                topic=note
            )
        structured_model = self.llm.with_structured_output(Resource)

        resources = await structured_model.ainvoke(prompt)

        state["resources"] = [
                {
                    "title": res.title,
                    "url": res.url,
                    "reason": res.reason
                } for res in resources
                ]

        return state


    async def format_final_output(self, state: NoMaState) -> NoMaState:
        """`Node`: Format the final output including title, tags, note, and resources."""

        md = MDBuilder()

        title = str(state['note_title']).strip() or "Untitled Note"
        state['output_file_name'] = f"{title.lower().replace(' ', '_')}.md"

        md.set_title(title)

        for tag in list(state['topic_tags'] or []):
            md.add_topic_tag(tag)

        md.add_paragraph(state["synthesized_note"] or "")

        resources = state["resources"] or []
        if len(resources) > 0:
            md.add_heading("Resources", level=1)
            for res in resources:
                resource_line = f"- [{res['title']}]({res['url']}): {res['reason']}"
                md.add_paragraph(resource_line)

        state["final_output"] = md.build()

        return state

    async def should_fetch_resources(self, state: NoMaState) -> Literal["fetch_resources", "format_output"]:
        """`Edge`: Decide whether to fetch resources based on internet availability.""" 

        if state.get("has_internet", False):
            return "fetch_resources"

        return "format_output"

    async def merge_metadata(self, state: NoMaState) -> NoMaState:
        """`Node`: Merge title and tags into the final output."""
        if "resources" not in state:
            state["resources"] = None
        return state

