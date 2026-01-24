"""Entity graph Pydantic models."""
from typing import List

from pydantic import BaseModel


class GraphNode(BaseModel):
    """A node in the entity graph."""

    id: str
    label: str
    entity_type: str
    event_count: int
    first_seen: str
    last_seen: str


class GraphEdge(BaseModel):
    """An edge connecting two entities."""

    source: str
    target: str
    weight: int
    edge_type: str


class GraphResponse(BaseModel):
    """Response containing graph nodes and edges."""

    nodes: List[GraphNode]
    edges: List[GraphEdge]
