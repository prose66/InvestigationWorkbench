"""Entity-related Pydantic models."""
from typing import List, Optional

from pydantic import BaseModel


class Entity(BaseModel):
    """An entity (host, user, IP, etc.)."""

    entity_type: str
    entity_value: str
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    event_count: int = 0


class EntitySummary(BaseModel):
    """Summary statistics for an entity."""

    entity_type: str
    entity_value: str
    first_seen: str
    last_seen: str
    total_events: int
    source_systems: List[str]
    event_types: List[str]


class RelatedEntity(BaseModel):
    """An entity related to another entity."""

    entity_type: str
    entity_value: str
    count: int
    first_seen: str
    last_seen: str


class EntityRelationships(BaseModel):
    """All relationships for an entity."""

    entity_type: str
    entity_value: str
    related_hosts: List[RelatedEntity] = []
    related_users: List[RelatedEntity] = []
    related_ips: List[RelatedEntity] = []
    related_processes: List[RelatedEntity] = []
    related_hashes: List[RelatedEntity] = []
