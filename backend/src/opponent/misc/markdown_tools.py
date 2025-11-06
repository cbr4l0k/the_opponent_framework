from dataclasses import dataclass, field, fields
from collections import defaultdict
from typing import List

@dataclass
class MDBuilder:
    """
    Class to generate markdown formatted notes. Adding components one at a time.
    """
    title: str = ""
    # Tags:
    #	| Source	<#s/>: opponent 
    #	| Context	<#c/>: selftudy 
    #	| Topic		<#t/>: Must be added separately
    tags: List[str] = field(
            default_factory=lambda: ["#s/opponent", "#c/selfstudy"]
            )
    content: str = ""

    def set_title(self, title: str) -> None:
        """Set the title of the note."""
        self.title = title

    def add_topic_tag(self, tag: str) -> None:
        """Add a topic tag to the note."""
        if not tag.startswith("#c/"):
            tag = f"#c/{tag}"
        if tag not in self.tags:
            self.tags.append(tag)

    def add_heading(self, heading: str, level: int = 1) -> None:
        """Add a heading to the content."""
        self.content += f"\n{'#' * level} {heading}\n"

    def add_paragraph(self, paragraph: str) -> None:
        """Add a paragraph to the content."""
        self.content += f"\n{paragraph}\n"

    def generate_metadata(self) -> None:
        """Generate the frontmatter metadata for the note."""
        assert self.title, "Title must be set before generating metadata."
        metadata = "---\n"
        title = self.title
        # Quote title if it contains YAML special characters (: [ ] { } , & * # ? | - < > = ! % @ \)
        if any(char in title for char in ':[]{},"\'&*#?|-<>=!%@\\'):
            title = f'"{title}"'
        metadata += f"title: {title}\n"
        metadata += "---\n"

        self.content = metadata + self.content

    def build(self) -> str:
        """Build the complete markdown note."""
        self.generate_metadata()
        return self.content

