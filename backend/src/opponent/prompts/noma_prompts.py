"""
Prompts for the Noma method note creation.
"""

NOMA_SYNTHESIS_PROMPT = """You are synthesizing reflections into a coherent note using the NoMa method.

The user has provided these reflections:

INTERESTING: {interesting}

REMINDS ME: {reminds_me}

SIMILAR BECAUSE: {similar_because}

DIFFERENT BECAUSE: {different_because}

IMPORTANT BECAUSE: {important_because}

Create a single, flowing note that naturally integrates all these reflections.

CRITICAL RULES:
- Write ONLY the note content itself
- NO meta-commentary (no "Here is your note", "Based on", etc.)
- NO section headers for the 5 prompts
- Flow naturally and weave ideas together seamlessly
- Use clear, direct language
- Maintain logical progression
- Make it complete and self-contained
- Don't extend beyond the provided reflections

Output the note now:"""


NOMA_RESOURCE_SEARCH_PROMPT = """Based on this note about {topic}, find 2-5 high-prestige resources.

SELECTION CRITERIA:
- Only high-prestige sources: peer-reviewed journals, established publishers, recognized experts, reputable institutions
- Books: major academic presses, well-reviewed works by recognized authorities
- Articles: Nature, Science, academic journals, established publications (not blogs)
- Videos: university lectures, documentary series, established educational platforms

For each resource provide:
1. Title
2. URL (if available)
3. One sentence explaining why it's valuable

Return as JSON array: [{{"title": "...", "url": "...", "reason": "..."}}]"""

NOMA_TITLE_PROMPT = """Based on this note, generate a concise title.

Note:
{note}

INSTRUCTIONS:
- Create a clear, descriptive title (3-8 words)
- Capture the main idea or theme
- Make it specific and informative

Output only title:"""

NOMA_TAGS_PROMPT = """Based on this note, identify 2-4 relevant topic tags.

Note:
{note}

INSTRUCTIONS:
- Identify 2-4 key topics/themes from the note
- Tags should be single words or short phrases (e.g., "neuroplasticity", "learning", "brain-science")
- DO NOT include # symbols in tags (they will be added automatically)
- DO NOT include source (#s/) or context (#c/) tags (already included by default)

Return as JSON:
{{"tags": ["tag1", "tag2", "tag3"]}}

Output only the JSON, no additional text."""

NOMA_PROMPTS = {
    "synthesis": NOMA_SYNTHESIS_PROMPT,
    "resources": NOMA_RESOURCE_SEARCH_PROMPT,
    "title": NOMA_TITLE_PROMPT,
    "tags": NOMA_TAGS_PROMPT,
}
