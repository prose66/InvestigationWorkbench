"""Entity graph visualization view."""
from __future__ import annotations

import json
import streamlit as st
import streamlit.components.v1 as components

from services.db import query_df
from services.entities import ENTITY_TYPES, entity_options
from services.graph import build_entity_graph, get_entity_connections
from state import queue_entity_navigation


# Color scheme for entity types
ENTITY_COLORS = {
    "host": "#4a90d9",      # Blue
    "user": "#50c878",      # Green
    "ip": "#ff6b6b",        # Red
    "hash": "#9b59b6",      # Purple
    "process": "#f39c12",   # Orange
}


def generate_vis_html(nodes, edges, height: int = 500) -> str:
    """Generate vis.js HTML for the graph visualization."""
    
    # Convert nodes to vis.js format
    vis_nodes = []
    for node in nodes:
        vis_nodes.append({
            "id": node.id,
            "label": node.label[:30] + "..." if len(node.label) > 30 else node.label,
            "title": f"{node.entity_type}: {node.label}<br>Events: {node.event_count}<br>First: {node.first_seen}<br>Last: {node.last_seen}",
            "color": ENTITY_COLORS.get(node.entity_type, "#999999"),
            "size": min(10 + node.event_count // 10, 50),
            "font": {"color": "#ffffff"},
        })
    
    # Convert edges to vis.js format
    vis_edges = []
    for edge in edges:
        vis_edges.append({
            "from": edge.source,
            "to": edge.target,
            "value": edge.weight,
            "title": f"Co-occurrences: {edge.weight}",
        })
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
        <style type="text/css">
            #graph {{
                width: 100%;
                height: {height}px;
                border: 1px solid #333;
                background-color: #1a1a2e;
            }}
            .legend {{
                position: absolute;
                top: 10px;
                right: 10px;
                background: rgba(0,0,0,0.7);
                padding: 10px;
                border-radius: 5px;
                font-family: sans-serif;
                font-size: 12px;
                color: white;
            }}
            .legend-item {{
                display: flex;
                align-items: center;
                margin: 4px 0;
            }}
            .legend-color {{
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 8px;
            }}
        </style>
    </head>
    <body>
        <div id="graph"></div>
        <div class="legend">
            <div class="legend-item"><div class="legend-color" style="background: #4a90d9"></div>Host</div>
            <div class="legend-item"><div class="legend-color" style="background: #50c878"></div>User</div>
            <div class="legend-item"><div class="legend-color" style="background: #ff6b6b"></div>IP</div>
            <div class="legend-item"><div class="legend-color" style="background: #9b59b6"></div>Hash</div>
            <div class="legend-item"><div class="legend-color" style="background: #f39c12"></div>Process</div>
        </div>
        <script type="text/javascript">
            var nodes = new vis.DataSet({json.dumps(vis_nodes)});
            var edges = new vis.DataSet({json.dumps(vis_edges)});
            
            var container = document.getElementById('graph');
            var data = {{ nodes: nodes, edges: edges }};
            var options = {{
                nodes: {{
                    shape: 'dot',
                    borderWidth: 2,
                    shadow: true,
                    font: {{ size: 12 }}
                }},
                edges: {{
                    width: 1,
                    color: {{ color: '#666666', highlight: '#ffffff' }},
                    smooth: {{ type: 'continuous' }},
                    scaling: {{
                        min: 1,
                        max: 8,
                        label: {{ enabled: false }}
                    }}
                }},
                physics: {{
                    forceAtlas2Based: {{
                        gravitationalConstant: -50,
                        centralGravity: 0.01,
                        springLength: 100,
                        springConstant: 0.08
                    }},
                    maxVelocity: 50,
                    solver: 'forceAtlas2Based',
                    stabilization: {{ iterations: 150 }}
                }},
                interaction: {{
                    hover: true,
                    tooltipDelay: 100,
                    zoomView: true,
                    dragView: true
                }}
            }};
            
            var network = new vis.Network(container, data, options);
            
            // Double-click to navigate
            network.on("doubleClick", function(params) {{
                if (params.nodes.length > 0) {{
                    var nodeId = params.nodes[0];
                    // Post message to parent for navigation
                    window.parent.postMessage({{type: 'entityClick', nodeId: nodeId}}, '*');
                }}
            }});
        </script>
    </body>
    </html>
    """
    return html


def page_entity_graph(case_id: str) -> None:
    """Entity relationship graph visualization page."""
    st.subheader("Entity Relationship Graph")
    
    st.markdown("""
    Visualize how entities (hosts, users, IPs, processes) are connected through shared events.
    Larger nodes indicate more events, thicker edges indicate more co-occurrences.
    """)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        entity_type = st.selectbox("Entity Type", ENTITY_TYPES, key="graph_entity_type")
        entity_list = entity_options(case_id, entity_type)
        entity_value = st.selectbox(
            "Entity Value",
            [""] + entity_list,
            key="graph_entity_value",
        )
    
    with col2:
        max_nodes = st.slider("Max Nodes", 10, 100, 40, key="graph_max_nodes")
        min_weight = st.slider("Min Co-occurrences", 1, 20, 1, key="graph_min_weight")
    
    if not entity_value:
        st.info("Select an entity to visualize its relationships.")
        return
    
    # Build the graph
    with st.spinner("Building relationship graph..."):
        nodes, edges = build_entity_graph(
            case_id,
            entity_type,
            entity_value,
            max_nodes=max_nodes,
            min_edge_weight=min_weight,
        )
    
    if not nodes:
        st.warning("No data found for this entity.")
        return
    
    st.markdown(f"**Graph:** {len(nodes)} entities, {len(edges)} connections")
    
    # Render the graph
    graph_html = generate_vis_html(nodes, edges, height=500)
    components.html(graph_html, height=520)
    
    st.caption("Double-click a node to navigate to that entity. Drag to pan, scroll to zoom.")
    
    # Also show tabular view
    with st.expander("View as Table"):
        connections_df = get_entity_connections(case_id, entity_type, entity_value)
        if connections_df.empty:
            st.info("No connections found.")
        else:
            st.dataframe(connections_df, use_container_width=True)
            
            # Quick navigation
            st.markdown("##### Quick Navigate")
            for _, row in connections_df.head(10).iterrows():
                col1, col2 = st.columns([3, 1])
                col1.write(f"**{row['entity_type']}:** {row['entity_value']} ({row['co_occurrences']} events)")
                if col2.button("Open", key=f"nav_{row['entity_type']}_{row['entity_value']}"):
                    queue_entity_navigation(row["entity_type"], row["entity_value"])
                    st.rerun()
