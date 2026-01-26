"""Entity-related API endpoints."""
from typing import List

from fastapi import APIRouter, HTTPException, Query

from api.services.db import list_cases, query_df, query_one
from api.services.entities import (
    RELATED_ENTITY_MAP,
    entity_options,
    entity_where_clause,
    load_entity_config,
)
from api.schemas.entities import Entity, EntitySummary, RelatedEntity, EntityRelationships

router = APIRouter(prefix="/cases/{case_id}", tags=["entities"])


@router.get("/entity-types")
def get_entity_types(case_id: str):
    """Get configured entity types for a case.

    Returns the entity types from case_schema.yaml if configured,
    otherwise returns the default entity types.
    """
    cases = list_cases()
    if case_id not in cases:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")

    entity_types, _ = load_entity_config(case_id)
    return {"entity_types": entity_types}


@router.get("/entities", response_model=List[Entity])
def get_entities(
    case_id: str,
    entity_type: str = Query(...),
    limit: int = Query(default=100, ge=1, le=500),
):
    """Get entities of a specific type for a case."""
    cases = list_cases()
    if case_id not in cases:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")

    # Validate entity type against case config
    entity_types, _ = load_entity_config(case_id)
    if entity_type not in entity_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid entity type: {entity_type}. Valid types: {entity_types}",
        )

    entity_values = entity_options(case_id, entity_type, limit=limit)

    # Get stats for each entity
    entities = []
    for value in entity_values[:limit]:
        entity_clause, entity_params = entity_where_clause(case_id, entity_type, value)
        stats = query_one(
            case_id,
            f"""
            SELECT MIN(e.event_ts) AS first_seen,
                   MAX(e.event_ts) AS last_seen,
                   COUNT(*) AS event_count
            FROM events e
            WHERE e.case_id = ? AND {entity_clause}
            """,
            tuple([case_id] + entity_params),
        )
        entities.append(
            Entity(
                entity_type=entity_type,
                entity_value=value,
                first_seen=stats["first_seen"] if stats else None,
                last_seen=stats["last_seen"] if stats else None,
                event_count=stats["event_count"] if stats else 0,
            )
        )

    return entities


@router.get("/entity/{entity_type}/{entity_value}", response_model=EntitySummary)
def get_entity_summary(case_id: str, entity_type: str, entity_value: str):
    """Get summary for a specific entity."""
    cases = list_cases()
    if case_id not in cases:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")

    entity_types, _ = load_entity_config(case_id)
    if entity_type not in entity_types:
        raise HTTPException(status_code=400, detail=f"Invalid entity type: {entity_type}")

    entity_clause, entity_params = entity_where_clause(case_id, entity_type, entity_value)

    summary = query_one(
        case_id,
        f"""
        SELECT MIN(e.event_ts) AS first_seen,
               MAX(e.event_ts) AS last_seen,
               COUNT(*) AS total_events
        FROM events e
        WHERE e.case_id = ? AND {entity_clause}
        """,
        tuple([case_id] + entity_params),
    )

    if not summary or summary["total_events"] == 0:
        raise HTTPException(status_code=404, detail=f"Entity not found: {entity_type}={entity_value}")

    # Get source systems
    sources_df = query_df(
        case_id,
        f"""
        SELECT DISTINCT e.source_system
        FROM events e
        WHERE e.case_id = ? AND {entity_clause}
        """,
        tuple([case_id] + entity_params),
    )

    # Get event types
    types_df = query_df(
        case_id,
        f"""
        SELECT DISTINCT e.event_type
        FROM events e
        WHERE e.case_id = ? AND {entity_clause}
        """,
        tuple([case_id] + entity_params),
    )

    return EntitySummary(
        entity_type=entity_type,
        entity_value=entity_value,
        first_seen=summary["first_seen"],
        last_seen=summary["last_seen"],
        total_events=summary["total_events"],
        source_systems=sources_df["source_system"].tolist() if not sources_df.empty else [],
        event_types=types_df["event_type"].tolist() if not types_df.empty else [],
    )


@router.get("/entity/{entity_type}/{entity_value}/related", response_model=EntityRelationships)
def get_entity_relationships(
    case_id: str,
    entity_type: str,
    entity_value: str,
    limit: int = Query(default=15, ge=1, le=50),
):
    """Get related entities for a specific entity."""
    cases = list_cases()
    if case_id not in cases:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")

    entity_types, _ = load_entity_config(case_id)
    if entity_type not in entity_types:
        raise HTTPException(status_code=400, detail=f"Invalid entity type: {entity_type}")

    entity_clause, entity_params = entity_where_clause(case_id, entity_type, entity_value)
    base_where = f"e.case_id = ? AND {entity_clause}"
    base_params = [case_id] + entity_params

    relationships = EntityRelationships(
        entity_type=entity_type,
        entity_value=entity_value,
    )

    # Get related entities based on type
    related_groups = RELATED_ENTITY_MAP.get(entity_type, [])

    for title, field, target_type in related_groups:
        related_df = query_df(
            case_id,
            f"""
            SELECT
              e.{field} AS value,
              COUNT(*) AS count,
              MIN(e.event_ts) AS first_seen,
              MAX(e.event_ts) AS last_seen
            FROM events e
            WHERE {base_where}
              AND e.{field} IS NOT NULL
              AND e.{field} != ''
            GROUP BY e.{field}
            ORDER BY count DESC
            LIMIT ?
            """,
            tuple(base_params + [limit]),
        )

        related_entities = [
            RelatedEntity(
                entity_type=target_type,
                entity_value=row["value"],
                count=int(row["count"]),
                first_seen=row["first_seen"],
                last_seen=row["last_seen"],
            )
            for _, row in related_df.iterrows()
        ]

        # Assign to appropriate field
        if target_type == "host":
            relationships.related_hosts = related_entities
        elif target_type == "user":
            relationships.related_users = related_entities
        elif target_type == "ip":
            if not relationships.related_ips:
                relationships.related_ips = related_entities
            else:
                relationships.related_ips.extend(related_entities)
        elif target_type == "process":
            relationships.related_processes = related_entities
        elif target_type == "hash":
            relationships.related_hashes = related_entities

    return relationships
