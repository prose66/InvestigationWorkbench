"""Timeline marker Pydantic models."""
from typing import Optional

from pydantic import BaseModel


class Marker(BaseModel):
    """A timeline marker."""

    marker_id: int
    marker_ts: str
    label: str
    description: Optional[str] = None
    color: str = "#ff6b6b"

    class Config:
        from_attributes = True


class MarkerCreate(BaseModel):
    """Create a new timeline marker."""

    marker_ts: str
    label: str
    description: Optional[str] = None
    color: str = "#ff6b6b"
