"use client";

import { useParams, useSearchParams } from "next/navigation";
import { EntitySelector } from "@/components/entity/EntitySelector";
import { useEntitySummary, useEntityRelationships } from "@/hooks/useEntities";
import { usePivotContext } from "@/hooks/usePivotContext";
import { formatDate } from "@/lib/utils";

export default function EntityPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const caseId = params.caseId as string;

  const entityType = searchParams.get("type");
  const entityValue = searchParams.get("value");

  const { pivotToTimeline, pivotToTimelineSingle, navigateToEntity } =
    usePivotContext();

  const { data: summary, isLoading: loadingSummary } = useEntitySummary(
    caseId,
    entityType,
    entityValue
  );

  const { data: relationships, isLoading: loadingRelationships } =
    useEntityRelationships(caseId, entityType, entityValue);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Entity Analysis</h1>

      {/* Entity Selector - Main Area */}
      <EntitySelector caseId={caseId} />

      {/* Entity Details */}
      {entityType && entityValue && (
        <div className="space-y-6">
          {/* Header */}
          <div className="bg-card border rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-1">
              {entityType}: {entityValue}
            </h2>

            {loadingSummary ? (
              <p className="text-muted-foreground">Loading...</p>
            ) : summary ? (
              <div className="mt-4 grid gap-4 md:grid-cols-4">
                <div>
                  <p className="text-sm text-muted-foreground">First Seen</p>
                  <p className="font-medium">{formatDate(summary.first_seen)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Last Seen</p>
                  <p className="font-medium">{formatDate(summary.last_seen)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total Events</p>
                  <p className="font-medium">
                    {summary.total_events.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Sources</p>
                  <p className="font-medium">{summary.source_systems.length}</p>
                </div>
              </div>
            ) : (
              <p className="text-muted-foreground mt-2">Entity not found</p>
            )}

            {/* Action Buttons */}
            <div className="mt-4 flex gap-2">
              <button
                onClick={() => pivotToTimelineSingle(entityType, entityValue)}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm"
              >
                View All Events
              </button>
              <button
                onClick={() => pivotToTimeline(entityType, entityValue)}
                className="px-4 py-2 border rounded-md text-sm hover:bg-muted"
              >
                Add to Filters
              </button>
            </div>
          </div>

          {/* Related Entities */}
          {relationships && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Related Entities</h3>
              <p className="text-sm text-muted-foreground">
                Entities that appear in the same events as {entityType}=
                {entityValue}
              </p>

              <div className="grid gap-4 md:grid-cols-2">
                {relationships.related_hosts.length > 0 && (
                  <RelatedEntityList
                    title="Hosts"
                    entities={relationships.related_hosts}
                    onPivot={(value) => pivotToTimeline("host", value)}
                    onPivotSingle={(value) =>
                      pivotToTimelineSingle("host", value)
                    }
                    onNavigate={(value) => navigateToEntity("host", value)}
                  />
                )}
                {relationships.related_users.length > 0 && (
                  <RelatedEntityList
                    title="Users"
                    entities={relationships.related_users}
                    onPivot={(value) => pivotToTimeline("user", value)}
                    onPivotSingle={(value) =>
                      pivotToTimelineSingle("user", value)
                    }
                    onNavigate={(value) => navigateToEntity("user", value)}
                  />
                )}
                {relationships.related_ips.length > 0 && (
                  <RelatedEntityList
                    title="IPs"
                    entities={relationships.related_ips}
                    onPivot={(value) => pivotToTimeline("ip", value)}
                    onPivotSingle={(value) =>
                      pivotToTimelineSingle("ip", value)
                    }
                    onNavigate={(value) => navigateToEntity("ip", value)}
                  />
                )}
                {relationships.related_processes.length > 0 && (
                  <RelatedEntityList
                    title="Processes"
                    entities={relationships.related_processes}
                    onPivot={(value) => pivotToTimeline("process", value)}
                    onPivotSingle={(value) =>
                      pivotToTimelineSingle("process", value)
                    }
                    onNavigate={(value) => navigateToEntity("process", value)}
                  />
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function RelatedEntityList({
  title,
  entities,
  onPivot,
  onPivotSingle,
  onNavigate,
}: {
  title: string;
  entities: Array<{
    entity_type: string;
    entity_value: string;
    count: number;
    first_seen: string;
    last_seen: string;
  }>;
  onPivot: (value: string) => void;
  onPivotSingle: (value: string) => void;
  onNavigate: (value: string) => void;
}) {
  return (
    <div className="bg-card border rounded-lg p-4">
      <h4 className="font-semibold mb-3">{title}</h4>
      <ul className="space-y-2">
        {entities.map((entity) => (
          <li
            key={entity.entity_value}
            className="flex items-center justify-between text-sm"
          >
            <button
              onClick={() => onNavigate(entity.entity_value)}
              className="text-blue-600 hover:underline truncate max-w-48"
            >
              {entity.entity_value}
            </button>
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground text-xs">
                {entity.count} events
              </span>
              <button
                onClick={() => onPivot(entity.entity_value)}
                className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs hover:bg-blue-200"
                title="Add to pivot filters (intersection)"
              >
                +Filter
              </button>
              <button
                onClick={() => onPivotSingle(entity.entity_value)}
                className="px-2 py-0.5 bg-gray-100 rounded text-xs hover:bg-gray-200"
                title="View all events for this entity"
              >
                View All
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
