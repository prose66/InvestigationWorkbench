"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  Network,
  ChevronDown,
  GitBranch,
  CircleDot,
  ArrowRight,
  Eye,
  Filter,
  Zap,
} from "lucide-react";
import { getEntityGraph } from "@/lib/api";
import { ENTITY_TYPES, type EntityType } from "@/lib/types";
import { useEntities } from "@/hooks/useEntities";
import { usePivotContext } from "@/hooks/usePivotContext";
import { PivotChain } from "@/components/entity/PivotChain";
import { cn } from "@/lib/utils";

const entityTypeColors: Record<string, string> = {
  host: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  user: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  ip: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  process: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  hash: "bg-pink-500/20 text-pink-400 border-pink-500/30",
};

export default function GraphPage() {
  const params = useParams();
  const caseId = params.caseId as string;
  const [entityType, setEntityType] = useState<EntityType>("host");
  const [entityValue, setEntityValue] = useState("");
  const [selectedEntity, setSelectedEntity] = useState<{
    type: string;
    value: string;
  } | null>(null);

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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (entityValue) {
      setSelectedEntity({ type: entityType, value: entityValue });
    }
  };

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

      {/* Graph Display */}
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

      {graph && (
        <div className="grid gap-6 md:grid-cols-2">
          {/* Nodes List */}
          <div className="metric-card">
            <div className="flex items-center gap-2 mb-4">
              <CircleDot className="w-4 h-4 text-cyan" />
              <h3 className="font-semibold text-foreground">
                Nodes ({graph.nodes.length})
              </h3>
            </div>
            <div className="space-y-2 max-h-96 overflow-auto">
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
                        entityTypeColors[node.entity_type] ||
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
            <div className="space-y-2 max-h-96 overflow-auto">
              {graph.edges.map((edge, idx) => {
                const sourceNode = graph.nodes.find((n) => n.id === edge.source);
                const targetNode = graph.nodes.find((n) => n.id === edge.target);
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
                          entityTypeColors[sourceNode?.entity_type || ""] ||
                            "bg-secondary border-border"
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
                          entityTypeColors[targetNode?.entity_type || ""] ||
                            "bg-secondary border-border"
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
                      <span className="text-xs font-medium">
                        {edge.weight}
                      </span>
                    </div>
                  </div>
                );
              })}
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
