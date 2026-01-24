"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import dynamic from "next/dynamic";
import {
  Network,
  ChevronDown,
  GitBranch,
  CircleDot,
  ArrowRight,
  Eye,
  Filter,
  Zap,
  Maximize2,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import { getEntityGraph } from "@/lib/api";
import { ENTITY_TYPES, type EntityType } from "@/lib/types";
import { useEntities } from "@/hooks/useEntities";
import { usePivotContext } from "@/hooks/usePivotContext";
import { PivotChain } from "@/components/entity/PivotChain";
import { cn } from "@/lib/utils";

// Dynamically import ForceGraph2D to avoid SSR issues
const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full">
      <div className="inline-block animate-spin rounded-full h-8 w-8 border-2 border-cyan border-t-transparent" />
    </div>
  ),
});

const entityTypeColors: Record<string, string> = {
  host: "#3b82f6", // blue
  user: "#10b981", // emerald
  ip: "#a855f7", // purple
  process: "#f59e0b", // amber
  hash: "#ec4899", // pink
};

const entityTypeBadgeColors: Record<string, string> = {
  host: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  user: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  ip: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  process: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  hash: "bg-pink-500/20 text-pink-400 border-pink-500/30",
};

interface GraphNode {
  id: string;
  label: string;
  entity_type: string;
  event_count: number;
  color?: string;
  size?: number;
}

interface GraphLink {
  source: string;
  target: string;
  weight: number;
}

export default function GraphPage() {
  const params = useParams();
  const caseId = params.caseId as string;
  const [entityType, setEntityType] = useState<EntityType>("host");
  const [entityValue, setEntityValue] = useState("");
  const [selectedEntity, setSelectedEntity] = useState<{
    type: string;
    value: string;
  } | null>(null);
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const graphRef = useRef<any>(null);

  const { navigateToEntity, pivotToTimeline } = usePivotContext();
  const { data: entities } = useEntities(caseId, entityType, 50);

  const { data: graph, isLoading } = useQuery({
    queryKey: ["graph", caseId, selectedEntity?.type, selectedEntity?.value],
    queryFn: () =>
      getEntityGraph(
        caseId,
        selectedEntity!.type,
        selectedEntity!.value,
        50,
        1
      ),
    enabled: !!selectedEntity,
  });

  // Transform graph data for force-graph
  const graphData = graph
    ? {
        nodes: graph.nodes.map((node) => ({
          ...node,
          color: entityTypeColors[node.entity_type] || "#6b7280",
          size: Math.max(5, Math.min(20, Math.log(node.event_count + 1) * 3)),
        })),
        links: graph.edges.map((edge) => ({
          source: edge.source,
          target: edge.target,
          weight: edge.weight,
        })),
      }
    : { nodes: [], links: [] };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (entityValue) {
      setSelectedEntity({ type: entityType, value: entityValue });
    }
  };

  const handleNodeClick = useCallback(
    (node: GraphNode) => {
      pivotToTimeline(node.entity_type, node.label);
    },
    [pivotToTimeline]
  );

  const handleNodeRightClick = useCallback(
    (node: GraphNode) => {
      navigateToEntity(node.entity_type, node.label);
    },
    [navigateToEntity]
  );

  const handleZoomIn = () => {
    if (graphRef.current) {
      graphRef.current.zoom(graphRef.current.zoom() * 1.5, 300);
    }
  };

  const handleZoomOut = () => {
    if (graphRef.current) {
      graphRef.current.zoom(graphRef.current.zoom() / 1.5, 300);
    }
  };

  const handleFitView = () => {
    if (graphRef.current) {
      graphRef.current.zoomToFit(400, 50);
    }
  };

  // Auto-fit when graph loads
  useEffect(() => {
    if (graph && graphRef.current) {
      setTimeout(() => {
        graphRef.current?.zoomToFit(400, 50);
      }, 500);
    }
  }, [graph]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-cyan/10 pulse-glow">
          <Network className="w-5 h-5 text-cyan" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-foreground">Entity Graph</h1>
          <p className="text-muted-foreground text-sm">
            Visualize relationships between entities in your case
          </p>
        </div>
      </div>

      {/* Pivot Chain */}
      <PivotChain />

      {/* Entity Selection */}
      <form
        onSubmit={handleSubmit}
        className="metric-card flex flex-wrap gap-4 items-end"
      >
        <div>
          <label className="block text-xs text-muted-foreground uppercase tracking-wider font-medium mb-2">
            Entity Type
          </label>
          <div className="relative">
            <select
              value={entityType}
              onChange={(e) => setEntityType(e.target.value as EntityType)}
              className={cn(
                "appearance-none px-4 py-2.5 pr-10 rounded-lg text-sm font-medium",
                "bg-secondary border border-border",
                "text-foreground cursor-pointer",
                "hover:border-cyan/30 focus:outline-none focus:border-cyan/50 focus:ring-2 focus:ring-cyan/20",
                "transition-all duration-200"
              )}
            >
              {ENTITY_TYPES.map((type) => (
                <option key={type} value={type}>
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
          </div>
        </div>

        <div className="flex-1 min-w-[200px]">
          <label className="block text-xs text-muted-foreground uppercase tracking-wider font-medium mb-2">
            Entity Value
          </label>
          <div className="relative">
            <select
              value={entityValue}
              onChange={(e) => setEntityValue(e.target.value)}
              className={cn(
                "w-full appearance-none px-4 py-2.5 pr-10 rounded-lg text-sm",
                "bg-secondary border border-border",
                "text-foreground cursor-pointer",
                "hover:border-cyan/30 focus:outline-none focus:border-cyan/50 focus:ring-2 focus:ring-cyan/20",
                "transition-all duration-200"
              )}
            >
              <option value="">Select an entity...</option>
              {entities?.map((e) => (
                <option key={e.entity_value} value={e.entity_value}>
                  {e.entity_value} ({e.event_count} events)
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
          </div>
        </div>

        <button
          type="submit"
          disabled={!entityValue}
          className="btn-primary flex items-center gap-2 disabled:opacity-50"
        >
          <GitBranch className="w-4 h-4" />
          Build Graph
        </button>
      </form>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-2 border-cyan border-t-transparent mb-3" />
            <p className="text-muted-foreground text-sm">
              Building entity graph...
            </p>
          </div>
        </div>
      )}

      {/* Graph Visualization */}
      {graph && (
        <div className="space-y-4">
          {/* Graph Canvas */}
          <div className="metric-card relative" style={{ height: "500px" }}>
            {/* Controls */}
            <div className="absolute top-4 right-4 z-10 flex gap-2">
              <button
                onClick={handleZoomIn}
                className={cn(
                  "p-2 rounded-lg",
                  "bg-secondary/80 border border-border backdrop-blur-sm",
                  "hover:border-cyan/30 transition-colors"
                )}
                title="Zoom in"
              >
                <ZoomIn className="w-4 h-4" />
              </button>
              <button
                onClick={handleZoomOut}
                className={cn(
                  "p-2 rounded-lg",
                  "bg-secondary/80 border border-border backdrop-blur-sm",
                  "hover:border-cyan/30 transition-colors"
                )}
                title="Zoom out"
              >
                <ZoomOut className="w-4 h-4" />
              </button>
              <button
                onClick={handleFitView}
                className={cn(
                  "p-2 rounded-lg",
                  "bg-secondary/80 border border-border backdrop-blur-sm",
                  "hover:border-cyan/30 transition-colors"
                )}
                title="Fit to view"
              >
                <Maximize2 className="w-4 h-4" />
              </button>
            </div>

            {/* Legend */}
            <div className="absolute top-4 left-4 z-10 p-3 rounded-lg bg-secondary/80 border border-border backdrop-blur-sm">
              <p className="text-xs text-muted-foreground uppercase tracking-wider font-medium mb-2">
                Entity Types
              </p>
              <div className="space-y-1">
                {Object.entries(entityTypeColors).map(([type, color]) => (
                  <div key={type} className="flex items-center gap-2 text-xs">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: color }}
                    />
                    <span className="text-muted-foreground capitalize">
                      {type}
                    </span>
                  </div>
                ))}
              </div>
              <p className="text-xs text-muted-foreground mt-3">
                Click: Add filter | Right-click: View entity
              </p>
            </div>

            {/* Hovered Node Info */}
            {hoveredNode && (
              <div className="absolute bottom-4 left-4 z-10 p-3 rounded-lg bg-secondary/90 border border-cyan/30 backdrop-blur-sm">
                <p className="text-xs text-cyan uppercase tracking-wider font-medium">
                  {hoveredNode.entity_type}
                </p>
                <p className="font-mono text-sm text-foreground">
                  {hoveredNode.label}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {hoveredNode.event_count} events
                </p>
              </div>
            )}

            {/* Force Graph */}
            <ForceGraph2D
              ref={graphRef}
              graphData={graphData}
              nodeLabel={(node: any) => `${node.entity_type}: ${node.label}`}
              nodeColor={(node: any) => node.color}
              nodeRelSize={6}
              nodeVal={(node: any) => node.size}
              linkColor={() => "hsl(220, 15%, 25%)"}
              linkWidth={(link: any) => Math.max(1, Math.log(link.weight + 1))}
              linkDirectionalParticles={2}
              linkDirectionalParticleWidth={(link: any) =>
                Math.max(1, Math.log(link.weight + 1))
              }
              linkDirectionalParticleColor={() => "hsl(173, 80%, 50%)"}
              backgroundColor="transparent"
              onNodeClick={handleNodeClick}
              onNodeRightClick={handleNodeRightClick}
              onNodeHover={(node: any) => setHoveredNode(node)}
              nodeCanvasObject={(node: any, ctx, globalScale) => {
                const label = node.label;
                const fontSize = 12 / globalScale;
                ctx.font = `${fontSize}px JetBrains Mono, monospace`;

                // Node circle
                ctx.beginPath();
                ctx.arc(node.x, node.y, node.size || 5, 0, 2 * Math.PI);
                ctx.fillStyle = node.color;
                ctx.fill();

                // Glow effect
                ctx.shadowColor = node.color;
                ctx.shadowBlur = 10;
                ctx.fill();
                ctx.shadowBlur = 0;

                // Label (only show if zoomed in enough)
                if (globalScale > 0.7) {
                  ctx.textAlign = "center";
                  ctx.textBaseline = "middle";
                  ctx.fillStyle = "hsl(210, 20%, 90%)";
                  ctx.fillText(
                    label.length > 15 ? label.slice(0, 15) + "..." : label,
                    node.x,
                    node.y + (node.size || 5) + fontSize
                  );
                }
              }}
            />
          </div>

          {/* Node and Edge Lists */}
          <div className="grid gap-6 md:grid-cols-2">
            {/* Nodes List */}
            <div className="metric-card">
              <div className="flex items-center gap-2 mb-4">
                <CircleDot className="w-4 h-4 text-cyan" />
                <h3 className="font-semibold text-foreground">
                  Nodes ({graph.nodes.length})
                </h3>
              </div>
              <div className="space-y-2 max-h-64 overflow-auto">
                {graph.nodes.map((node, index) => (
                  <div
                    key={node.id}
                    className={cn(
                      "flex items-center justify-between p-3 rounded-lg",
                      "bg-secondary/30 border border-border/30",
                      "hover:border-cyan/30 transition-all duration-200",
                      "fade-in-up"
                    )}
                    style={{ animationDelay: `${index * 30}ms` }}
                  >
                    <div className="flex items-center gap-3">
                      <span
                        className={cn(
                          "inline-block px-2 py-0.5 rounded text-xs font-medium border",
                          entityTypeBadgeColors[node.entity_type] ||
                            "bg-secondary text-foreground border-border"
                        )}
                      >
                        {node.entity_type}
                      </span>
                      <span className="font-mono text-sm text-foreground truncate max-w-[150px]">
                        {node.label}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground text-xs">
                        {node.event_count} events
                      </span>
                      <button
                        onClick={() =>
                          navigateToEntity(node.entity_type, node.label)
                        }
                        className={cn(
                          "p-1.5 rounded text-xs",
                          "bg-secondary text-muted-foreground border border-border",
                          "hover:text-foreground hover:border-cyan/30 transition-colors"
                        )}
                        title="View entity details"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() =>
                          pivotToTimeline(node.entity_type, node.label)
                        }
                        className={cn(
                          "p-1.5 rounded text-xs",
                          "bg-cyan/10 text-cyan border border-cyan/20",
                          "hover:bg-cyan/20 transition-colors"
                        )}
                        title="Add to filters"
                      >
                        <Filter className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Edges List */}
            <div className="metric-card">
              <div className="flex items-center gap-2 mb-4">
                <GitBranch className="w-4 h-4 text-cyan" />
                <h3 className="font-semibold text-foreground">
                  Connections ({graph.edges.length})
                </h3>
              </div>
              <div className="space-y-2 max-h-64 overflow-auto">
                {graph.edges.map((edge, idx) => {
                  const sourceNode = graph.nodes.find(
                    (n) => n.id === edge.source
                  );
                  const targetNode = graph.nodes.find(
                    (n) => n.id === edge.target
                  );
                  return (
                    <div
                      key={idx}
                      className={cn(
                        "flex items-center justify-between p-3 rounded-lg",
                        "bg-secondary/30 border border-border/30",
                        "fade-in-up"
                      )}
                      style={{ animationDelay: `${idx * 30}ms` }}
                    >
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        <span
                          className={cn(
                            "px-1.5 py-0.5 rounded text-xs border",
                            entityTypeBadgeColors[
                              sourceNode?.entity_type || ""
                            ] || "bg-secondary border-border"
                          )}
                        >
                          {sourceNode?.entity_type?.slice(0, 1).toUpperCase()}
                        </span>
                        <span className="font-mono text-xs text-foreground truncate max-w-[80px]">
                          {sourceNode?.label || edge.source}
                        </span>
                        <ArrowRight className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                        <span
                          className={cn(
                            "px-1.5 py-0.5 rounded text-xs border",
                            entityTypeBadgeColors[
                              targetNode?.entity_type || ""
                            ] || "bg-secondary border-border"
                          )}
                        >
                          {targetNode?.entity_type?.slice(0, 1).toUpperCase()}
                        </span>
                        <span className="font-mono text-xs text-foreground truncate max-w-[80px]">
                          {targetNode?.label || edge.target}
                        </span>
                      </div>
                      <div className="flex items-center gap-1 text-amber-400">
                        <Zap className="w-3 h-3" />
                        <span className="text-xs font-medium">{edge.weight}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      {!selectedEntity && (
        <div
          className={cn(
            "text-center py-16 rounded-xl",
            "bg-gradient-to-b from-secondary/30 to-transparent",
            "border border-border/50"
          )}
        >
          <Network className="w-12 h-12 text-muted-foreground mx-auto mb-4 opacity-50" />
          <p className="text-muted-foreground">
            Select an entity above to build a relationship graph
          </p>
        </div>
      )}
    </div>
  );
}
