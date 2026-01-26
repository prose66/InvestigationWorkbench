"""Entity relationship graph service."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import pandas as pd

from api.services.db import query_df
from api.services.entities import load_entity_config


@dataclass
class GraphNode:
    """A node in the entity graph."""
    id: str
    label: str
    entity_type: str
    event_count: int
    first_seen: str
    last_seen: str


@dataclass
class GraphEdge:
    """An edge connecting two entities."""
    source: str
    target: str
    weight: int  # Number of events where both entities appear
    edge_type: str  # e.g., "host-user", "user-ip"


def build_entity_graph(
    case_id: str,
    center_entity_type: str,
    center_entity_value: str,
    max_nodes: int = 50,
    min_edge_weight: int = 1,
) -> Tuple[List[GraphNode], List[GraphEdge]]:
    """Build a relationship graph centered on an entity.

    Args:
        case_id: Case identifier
        center_entity_type: Type of the center entity (host, user, ip, etc.)
        center_entity_value: Value of the center entity
        max_nodes: Maximum number of nodes to include
        min_edge_weight: Minimum co-occurrence count to create an edge

    Returns:
        Tuple of (nodes, edges)
    """
    nodes: Dict[str, GraphNode] = {}
    edges: List[GraphEdge] = []

    # Load entity config from case schema
    entity_types, entity_column_map = load_entity_config(case_id)

    # Build where clause for center entity
    center_cols = entity_column_map.get(center_entity_type, [center_entity_type])
    if len(center_cols) > 1:
        # Multiple columns (e.g., ip -> [src_ip, dest_ip])
        conditions = " OR ".join([f"e.{col} = ?" for col in center_cols])
        center_where = f"({conditions})"
        center_params = [center_entity_value] * len(center_cols)
    else:
        col = center_cols[0] if center_cols else center_entity_type
        center_where = f"e.{col} = ?"
        center_params = [center_entity_value]
    
    # Add center node
    center_id = f"{center_entity_type}:{center_entity_value}"
    center_stats = query_df(
        case_id,
        f"""
        SELECT COUNT(*) as count, MIN(event_ts) as first_seen, MAX(event_ts) as last_seen
        FROM events e
        WHERE case_id = ? AND {center_where}
        """,
        tuple([case_id] + center_params),
    )
    
    if not center_stats.empty:
        row = center_stats.iloc[0]
        nodes[center_id] = GraphNode(
            id=center_id,
            label=center_entity_value,
            entity_type=center_entity_type,
            event_count=int(row["count"]),
            first_seen=row["first_seen"] or "",
            last_seen=row["last_seen"] or "",
        )
    
    # Build related entity types from config: (display_type, column_name)
    related_cols: List[Tuple[str, str]] = []
    for etype in entity_types:
        if etype == center_entity_type:
            continue  # Skip the center entity type
        cols = entity_column_map.get(etype, [])
        for col in cols:
            related_cols.append((etype, col))
    
    # Query for related entities
    for rel_type, rel_col in related_cols:
        
        related_df = query_df(
            case_id,
            f"""
            SELECT 
                e.{rel_col} AS value,
                COUNT(*) AS count,
                MIN(e.event_ts) AS first_seen,
                MAX(e.event_ts) AS last_seen
            FROM events e
            WHERE e.case_id = ? AND {center_where}
              AND e.{rel_col} IS NOT NULL
              AND e.{rel_col} != ''
            GROUP BY e.{rel_col}
            ORDER BY count DESC
            LIMIT ?
            """,
            tuple([case_id] + center_params + [max_nodes]),
        )
        
        for _, row in related_df.iterrows():
            if row["count"] < min_edge_weight:
                continue
                
            node_id = f"{rel_type}:{row['value']}"
            
            # Add node if not exists
            if node_id not in nodes:
                nodes[node_id] = GraphNode(
                    id=node_id,
                    label=str(row["value"]),
                    entity_type=rel_type,
                    event_count=int(row["count"]),
                    first_seen=row["first_seen"] or "",
                    last_seen=row["last_seen"] or "",
                )
            
            # Add edge from center to this node
            edge_type = f"{center_entity_type}-{rel_type}"
            edges.append(GraphEdge(
                source=center_id,
                target=node_id,
                weight=int(row["count"]),
                edge_type=edge_type,
            ))
    
    # Limit total nodes
    if len(nodes) > max_nodes:
        # Keep center + top nodes by event count
        sorted_nodes = sorted(
            nodes.values(),
            key=lambda n: (n.id == center_id, n.event_count),
            reverse=True
        )[:max_nodes]
        kept_ids = {n.id for n in sorted_nodes}
        nodes = {n.id: n for n in sorted_nodes}
        edges = [e for e in edges if e.source in kept_ids and e.target in kept_ids]
    
    return list(nodes.values()), edges


def get_entity_connections(
    case_id: str,
    entity_type: str,
    entity_value: str,
) -> pd.DataFrame:
    """Get a summary of entity connections for tabular display."""
    nodes, edges = build_entity_graph(case_id, entity_type, entity_value, max_nodes=100)
    
    if not edges:
        return pd.DataFrame()
    
    # Convert to DataFrame
    data = []
    node_lookup = {n.id: n for n in nodes}
    
    for edge in edges:
        target_node = node_lookup.get(edge.target)
        if target_node:
            data.append({
                "entity_type": target_node.entity_type,
                "entity_value": target_node.label,
                "co_occurrences": edge.weight,
                "first_seen": target_node.first_seen,
                "last_seen": target_node.last_seen,
            })
    
    return pd.DataFrame(data)
