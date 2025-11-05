"""RAG retrieval utilities and chain construction."""

from typing import Any
from langchain_ollama import ChatOllama
from .vectorstore import VectorStore


class Retriever:
    """Handles RAG retrieval operations for various use cases."""

    def __init__(self, vectorstore: VectorStore, ollama_model: str, top_k: int = 5) -> None:
        """
        Initialize the retriever.

        Args:
            `vectorstore`: VectorStore instance
            `ollama_model`: Name of Ollama model for reranking/synthesis
            `top_k`: Default number of results to retrieve
        """
        self.vectorstore = vectorstore
        self.ollama_model = ollama_model
        self.top_k = top_k
        self.llm = ChatOllama(model=self.ollama_model, temperature=0)

    async def retrieve_for_linking(self, note_content: str, exclude_path: str) -> list[dict[str, Any]]:
        """
        Retrieve notes relevant for linking.

        Args:
            `note_content`: Content to find links for
            `exclude_path`: Path to exclude from results (the note itself)
        Returns:
            List of relevant notes with scores
        """
        # Extracting key concepts of the note
        concept_prompt = '\n'.join((
                "Extract 2-3 key concepts or themes from this note that would benefit from links to related notes.",
                "",
                "Note Content:",
                f"{note_content[:1000]}",
                "",
                "Return ONLY the concepts as a coma-separated list, nothing else."
                ))
        response = await self.llm.invoke(concept_prompt)
        concepts = response.content.strip()
        
        # Search using those concepts
        results = self.vectorstore.search(
                query=concepts,
                top_k=self.top_k * 2, # Later filter will reduce this number
                )

        # Filter out current notes and duplicates
        seen_paths = {exclude_path}
        filtered_results = []

        for result in results:
            path = result["metadata"].get("path", "")

            if path in seen_paths:
                continue

            seen_paths.add(path)
            filtered_results.append(result)

            if len(filtered_results) >= self.top_k:
                break

        return filtered_results

    async def retrieve_for_opposition(
        self, claim: str, context: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Retrieve evidence for opposing an argument.

        Args:
            `claim`: The claim to find counter-evidence for
            `context`: Optional additional context
        Returns:
            List of relevant counter-evidence with sources
        """
        full_query = f"{claim}\n\nContext: {context}" if context else claim

        # Strategy 1: Get notes tagged with #opponent
        opponent_tagged = self.vectorstore.search(
                query=full_query,
                top_k=self.top_k,
                filter_metadata={"tags": {"$contains": "opponent"}},
                )

        # Strategy 2: Search with opposition-focused phrasing
        opposition_query = f"arguments against {claim}, counerpoints to {claim}, challenges to {claim}"
        general_results = self.vectorstore.search(
                query=opposition_query,
                top_k=self.top_k,
                )

        # Mix and remove duplicates
        combined_results = {}
        for result in opponent_tagged + general_results:
            path = result['metadata']['path']
            if path not in combined_results:
                combined_results[path] = result

        if combined_results:
            # Re rank the files
            reranked = self._rerank_results(
                    query=claim,
                    results=list(combined_results.values()),
                    )
            return reranked[:self.top_k]
        return []


    async def retrieve_by_tag(self, tag: str, top_k: int | None = None) -> list[dict[str, Any]]:
        """
        Retrieve notes by tag (e.g., #opponent).

        Args:
            `tag`: Tag to filter by (without #)
            `top_k`: Optional override for number of results
        Returns:
            List of notes with the specified tag
        """
        k = top_k or self.top_k

        results = self.vectorstore.search(
                query="",
                top_k=k * 2, 
                filder_metadata={"tags": {"$contains": tag}},
                )

        raise NotImplementedError("Tag retrieval not implemented yet")

    def _rerank_results(self, query: str, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Rerank search results using LLM for better relevance.
        """
        rerank_prompt = '\n'.join((
            "You are evaluating search results for their ability to oppose or counter this claim:",
            "",
            f"CLAIM: {query}",
            "",
            "For each result below, assign a score from 0-10 based on:",
            "- How directly it contradicts or challenges the claim",
            "- Quality of counter-arguments or alternative perspectives",
            "- Relevance of evidence provided",
            "",
            "Results:"))

        for idx, result in enumerate(results, start=1):
            rerank_prompt += f"\n[{idx}] {result['content'][:500]}...\n"

        rerank_prompt += "Return ONLY a JSON array of scores in order, like: [8, 3, 6, 9, 2]\nDo not include any explanation, just the array."

        response = await self.llm.invoke(rerank_prompt)
        
        try: 
            # Parse scores
            import json
            scores = json.loads(response.content.strip())

            scored_results = [
                    {**result, 'rerank_score': score}
                    for result, score in zip(results, scores)
                    ]
            scored_results.sort(key=lambda x: x['rerank_score'], reverse=True)

            return scored_results
        except (json.JSONDecodeError, ValueError) as e:
          # If parsing fails, return original order
          print(f"⚠️  Failed to parse reranking scores, using original order: {e}")
          return results
        raise NotImplementedError()








