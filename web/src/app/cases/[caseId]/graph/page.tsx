"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { getEntityGraph } from "@/lib/api";
import { ENTITY_TYPES, type EntityType } from "@/lib/types";
import { useEntities } from "@/hooks/useEntities";
import { usePivotContext } from "@/hooks/usePivotContext";

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
      <h1 className="text-2xl font-bold">Entity Graph</h1>
      <p className="text-muted-foreground">
        Visualize relationships between entities in your case
      </p>

      {/* Entity Selection */}
      <form onSubmit={handleSubmit} className="flex gap-3 items-end">
        <div>
          <label className="block text-sm font-medium mb-1">Entity Type</label>
          <select
            value={entityType}
            onChange={(e) => setEntityType(e.target.value as EntityType)}
            className="px-3 py-2 border rounded-md bg-background"
          >
            {ENTITY_TYPES.map((type) => (
              <option key={type} value={type}>
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </option>
            ))}
          </select>
        </div>

        <div className="flex-1">
          <label className="block text-sm font-medium mb-1">Entity Value</label>
          <select
            value={entityValue}
            onChange={(e) => setEntityValue(e.target.value)}
            className="w-full px-3 py-2 border rounded-md bg-background"
          >
            <option value="">Select an entity...</option>
            {entities?.map((e) => (
              <option key={e.entity_value} value={e.entity_value}>
                {e.entity_value} ({e.event_count} events)
              </option>
            ))}
          </select>
        </div>

        <button
          type="submit"
          disabled={!entityValue}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md disabled:opacity-50"
        >
          Build Graph
        </button>
      </form>

      {/* Graph Display */}
      {isLoading && (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      )}

      {graph && (
        <div className="grid gap-6 md:grid-cols-2">
          {/* Nodes List */}
          <div className="bg-card border rounded-lg p-4">
            <h3 className="font-semibold mb-3">
              Nodes ({graph.nodes.length})
            </h3>
            <div className="space-y-2 max-h-96 overflow-auto">
              {graph.nodes.map((node) => (
                <div
                  key={node.id}
                  className="flex items-center justify-between p-2 bg-muted rounded text-sm"
                >
                  <div>
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-xs mr-2 ${
                        node.entity_type === "host"
                          ? "bg-blue-100 text-blue-800"
                          : node.entity_type === "user"
                            ? "bg-green-100 text-green-800"
                            : node.entity_type === "ip"
                              ? "bg-purple-100 text-purple-800"
                              : "bg-gray-100 text-gray-800"
                      }`}
                    >
                      {node.entity_type}
                    </span>
                    <span className="truncate">{node.label}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground text-xs">
                      {node.event_count} events
                    </span>
                    <button
                      onClick={() =>
                        navigateToEntity(node.entity_type, node.label)
                      }
                      className="px-2 py-0.5 border rounded text-xs hover:bg-background"
                    >
                      View
                    </button>
                    <button
                      onClick={() =>
                        pivotToTimeline(node.entity_type, node.label)
                      }
                      className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs"
                    >
                      +Filter
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Edges List */}
          <div className="bg-card border rounded-lg p-4">
            <h3 className="font-semibold mb-3">
              Connections ({graph.edges.length})
            </h3>
            <div className="space-y-2 max-h-96 overflow-auto">
              {graph.edges.map((edge, idx) => {
                const sourceNode = graph.nodes.find((n) => n.id === edge.source);
                const targetNode = graph.nodes.find((n) => n.id === edge.target);
                return (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-2 bg-muted rounded text-sm"
                  >
                    <div className="flex items-center gap-2">
                      <span className="truncate max-w-24">
                        {sourceNode?.label || edge.source}
                      </span>
                      <span className="text-muted-foreground">→</span>
                      <span className="truncate max-w-24">
                        {targetNode?.label || edge.target}
                      </span>
                    </div>
                    <span className="text-muted-foreground text-xs">
                      {edge.weight} co-occurrences
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {!selectedEntity && (
        <div className="text-center py-12 bg-muted/50 rounded-lg">
          <p className="text-muted-foreground">
            Select an entity above to build a relationship graph
          </p>
        </div>
      )}
    </div>
  );
}
