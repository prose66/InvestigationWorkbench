"""Entity graph API endpoints."""
from fastapi import APIRouter, HTTPException, Query

import sys
from pathlib import Path

# Add app directory to path to import services
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from services.db import list_cases
from services.entities import ENTITY_TYPES
from services.graph import build_entity_graph

from api.schemas.graph import GraphNode, GraphEdge, GraphResponse

router = APIRouter(prefix="/cases/{case_id}/graph", tags=["graph"])


@router.get("", response_model=GraphResponse)
def get_entity_graph(
    case_id: str,
    entity_type: str = Query(..., enum=ENTITY_TYPES),
    entity_value: str = Query(...),
    max_nodes: int = Query(default=50, ge=1, le=100),
    min_edge_weight: int = Query(default=1, ge=1),
):
    """Build an entity relationship graph centered on a specific entity."""
    cases = list_cases()
    if case_id not in cases:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")

    nodes, edges = build_entity_graph(
        case_id,
        entity_type,
        entity_value,
        max_nodes=max_nodes,
        min_edge_weight=min_edge_weight,
    )

    return GraphResponse(
        nodes=[
            GraphNode(
                id=n.id,
                label=n.label,
                entity_type=n.entity_type,
                event_count=n.event_count,
                first_seen=n.first_seen,
                last_seen=n.last_seen,
            )
            for n in nodes
        ],
        edges=[
            GraphEdge(
                source=e.source,
                target=e.target,
                weight=e.weight,
                edge_type=e.edge_type,
            )
            for e in edges
        ],
    )
