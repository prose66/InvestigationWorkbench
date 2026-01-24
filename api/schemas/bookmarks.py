"""Bookmark-related Pydantic models."""
from typing import Optional

from pydantic import BaseModel


class Bookmark(BaseModel):
    """A bookmarked event."""

    bookmark_id: int
    event_pk: int
    label: Optional[str] = None
    notes: Optional[str] = None
    created_at: str
    # Event details
    event_ts: Optional[str] = None
    source_system: Optional[str] = None
    event_type: Optional[str] = None
    host: Optional[str] = None
    user: Optional[str] = None
    message: Optional[str] = None

    class Config:
        from_attributes = True


class BookmarkCreate(BaseModel):
    """Create a new bookmark."""

    event_pk: int
    label: Optional[str] = None
    notes: Optional[str] = None


class BookmarkUpdate(BaseModel):
    """Update an existing bookmark."""

    label: Optional[str] = None
    notes: Optional[str] = None
