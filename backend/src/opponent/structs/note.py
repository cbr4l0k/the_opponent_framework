from pydantic import BaseModel, Field
from typing import Optional

class Resource(BaseModel):
    """A resource linked to a note, such as a URL or document."""
    title: str
    url: Optional[str] = None
    reason: str

class NoteTitle(BaseModel):
    """Metadata for a note, only generated title."""
    title: str

class NoteTags(BaseModel):
    """Metadata for a note, only generated tags."""
    tags: list[str] = Field(min_length=1, max_length=3)

class NoMaNote(BaseModel):
    """A plain markdown text created using the Noma method. No titles, tags, or sections."""
    content: str
    
