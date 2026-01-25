"use client";

import { useCallback } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { useRouter } from "next/navigation";
import {
  Users,
  Calendar,
  Activity,
  Database,
  Eye,
  Filter,
  Link2,
  Server,
  User,
  Globe,
  Cpu,
} from "lucide-react";
import { EntitySelector } from "@/components/entity/EntitySelector";
import { PivotChain } from "@/components/entity/PivotChain";
import { useEntitySummary, useEntityRelationships } from "@/hooks/useEntities";
import { usePivotContext } from "@/hooks/usePivotContext";
import { usePivotStore, createPivotEntity } from "@/stores/pivotStore";
import { formatDate } from "@/lib/utils";
import { cn } from "@/lib/utils";

// Hoisted outside component to prevent re-creation
const entityIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  host: Server,
  user: User,
  ip: Globe,
  process: Cpu,
};

export default function EntityPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const caseId = params.caseId as string;

  const entityType = searchParams.get("type");
  const entityValue = searchParams.get("value");

  const { pivotToTimeline, pivotToTimelineSingle, navigateToEntity } =
    usePivotContext();

  const { setPivotEntities } = usePivotStore();

  const { data: summary, isLoading: loadingSummary } = useEntitySummary(
    caseId,
    entityType,
    entityValue
  );

  const { data: relationships, isLoading: loadingRelationships } =
    useEntityRelationships(caseId, entityType, entityValue);

  // Pivot to timeline with BOTH current entity AND related entity (intersection)
  const pivotWithCurrentEntity = useCallback(
    (relatedType: string, relatedValue: string) => {
      const entities = [];

      // Add current entity first
      if (entityType && entityValue) {
        entities.push(createPivotEntity(entityType, entityValue));
      }

      // Add the related entity
      entities.push(createPivotEntity(relatedType, relatedValue));

      // Set both at once
      setPivotEntities(entities);

      // Navigate to timeline
      router.push(`/cases/${caseId}/timeline`);
    },
    [caseId, entityType, entityValue, router, setPivotEntities]
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-cyan/10 pulse-glow">
          <Users className="w-5 h-5 text-cyan" aria-hidden="true" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-foreground">Entity Analysis</h1>
          <p className="text-muted-foreground text-sm">
            Explore entities and their relationships
          </p>
        </div>
      </div>

      {/* Pivot Chain */}
      <PivotChain />

      {/* Entity Selector - Main Area */}
      <EntitySelector caseId={caseId} />

      {/* Entity Details */}
      {entityType && entityValue && (
        <div className="space-y-6 fade-in-up">
          {/* Entity Card */}
          <div className="metric-card">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-secondary">
                  {(() => {
                    const Icon = entityIcons[entityType] || Users;
                    return <Icon className="w-5 h-5 text-cyan" aria-hidden="true" />;
                  })()}
                </div>
                <div>
                  <p className="text-xs text-cyan uppercase tracking-wider font-semibold">
                    {entityType}
                  </p>
                  <h2 className="text-xl font-bold font-mono text-foreground">
                    {entityValue}
                  </h2>
                </div>
              </div>
            </div>

            {loadingSummary ? (
              <div className="flex items-center justify-center py-8">
                <div
                  className="inline-block animate-spin rounded-full h-6 w-6 border-2 border-cyan border-t-transparent"
                  role="status"
                  aria-label="Loading entity summary"
                />
              </div>
            ) : summary ? (
              <>
                {/* Stats Grid */}
                <div className="grid gap-4 md:grid-cols-4 mb-6">
                  <StatCard
                    icon={Calendar}
                    label="First Seen"
                    value={formatDate(summary.first_seen)}
                  />
                  <StatCard
                    icon={Calendar}
                    label="Last Seen"
                    value={formatDate(summary.last_seen)}
                  />
                  <StatCard
                    icon={Activity}
                    label="Total Events"
                    value={summary.total_events.toLocaleString()}
                    highlight
                  />
                  <StatCard
                    icon={Database}
                    label="Sources"
                    value={summary.source_systems.length.toString()}
                  />
                </div>

                {/* Action Buttons */}
                <div className="flex gap-3">
                  <button
                    onClick={() =>
                      pivotToTimelineSingle(entityType, entityValue)
                    }
                    className="btn-primary flex items-center gap-2"
                  >
                    <Eye className="w-4 h-4" aria-hidden="true" />
                    View All Events
                  </button>
                  <button
                    onClick={() => pivotToTimeline(entityType, entityValue)}
                    className={cn(
                      "flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium",
                      "bg-secondary border border-border",
                      "hover:border-cyan/30 hover:bg-secondary/80",
                      "transition-all duration-200"
                    )}
                  >
                    <Filter className="w-4 h-4" aria-hidden="true" />
                    Add to Filters
                  </button>
                </div>
              </>
            ) : (
              <div className="text-center py-8">
                <p className="text-muted-foreground">Entity not found</p>
              </div>
            )}
          </div>

          {/* Related Entities */}
          {relationships && (
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Link2 className="w-4 h-4 text-cyan" aria-hidden="true" />
                <h3 className="text-lg font-semibold text-foreground">
                  Related Entities
                </h3>
              </div>
              <p className="text-sm text-muted-foreground">
                Entities that appear in the same events as{" "}
                <span className="text-cyan font-mono">
                  {entityType}={entityValue}
                </span>
                . Click entity name or "+Filter" to see intersection.
              </p>

              <div className="grid gap-4 md:grid-cols-2">
                {relationships.related_hosts.length > 0 && (
                  <RelatedEntityList
                    title="Hosts"
                    icon={Server}
                    entities={relationships.related_hosts}
                    currentEntityType={entityType}
                    currentEntityValue={entityValue}
                    onPivotIntersection={(value) => pivotWithCurrentEntity("host", value)}
                    onPivotSingle={(value) =>
                      pivotToTimelineSingle("host", value)
                    }
                    onNavigate={(value) => navigateToEntity("host", value)}
                  />
                )}
                {relationships.related_users.length > 0 && (
                  <RelatedEntityList
                    title="Users"
                    icon={User}
                    entities={relationships.related_users}
                    currentEntityType={entityType}
                    currentEntityValue={entityValue}
                    onPivotIntersection={(value) => pivotWithCurrentEntity("user", value)}
                    onPivotSingle={(value) =>
                      pivotToTimelineSingle("user", value)
                    }
                    onNavigate={(value) => navigateToEntity("user", value)}
                  />
                )}
                {relationships.related_ips.length > 0 && (
                  <RelatedEntityList
                    title="IPs"
                    icon={Globe}
                    entities={relationships.related_ips}
                    currentEntityType={entityType}
                    currentEntityValue={entityValue}
                    onPivotIntersection={(value) => pivotWithCurrentEntity("ip", value)}
                    onPivotSingle={(value) =>
                      pivotToTimelineSingle("ip", value)
                    }
                    onNavigate={(value) => navigateToEntity("ip", value)}
                  />
                )}
                {relationships.related_processes.length > 0 && (
                  <RelatedEntityList
                    title="Processes"
                    icon={Cpu}
                    entities={relationships.related_processes}
                    currentEntityType={entityType}
                    currentEntityValue={entityValue}
                    onPivotIntersection={(value) => pivotWithCurrentEntity("process", value)}
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

function StatCard({
  icon: Icon,
  label,
  value,
  highlight = false,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div className="bg-secondary/30 border border-border/50 rounded-lg p-3">
      <div className="flex items-center gap-2 mb-1">
        <Icon className="w-3.5 h-3.5 text-muted-foreground" aria-hidden="true" />
        <p className="text-xs text-muted-foreground uppercase tracking-wider">
          {label}
        </p>
      </div>
      <p
        className={cn(
          "font-semibold tabular-nums",
          highlight ? "text-cyan text-lg" : "text-foreground text-sm"
        )}
      >
        {value}
      </p>
    </div>
  );
}

function RelatedEntityList({
  title,
  icon: Icon,
  entities,
  currentEntityType,
  currentEntityValue,
  onPivotIntersection,
  onPivotSingle,
  onNavigate,
}: {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  entities: Array<{
    entity_type: string;
    entity_value: string;
    count: number;
    first_seen: string;
    last_seen: string;
  }>;
  currentEntityType: string;
  currentEntityValue: string;
  onPivotIntersection: (value: string) => void;
  onPivotSingle: (value: string) => void;
  onNavigate: (value: string) => void;
}) {
  return (
    <div className="metric-card">
      <div className="flex items-center gap-2 mb-4">
        <Icon className="w-4 h-4 text-cyan" aria-hidden="true" />
        <h4 className="font-semibold text-foreground">{title}</h4>
        <span className="text-xs text-muted-foreground tabular-nums">
          ({entities.length})
        </span>
      </div>

      <ul className="space-y-2">
        {entities.map((entity, index) => (
          <li
            key={entity.entity_value}
            className={cn(
              "flex items-center justify-between p-2 rounded-lg",
              "bg-secondary/30 border border-border/30",
              "hover:border-cyan/30 transition-all duration-200",
              "fade-in-up"
            )}
            style={{ animationDelay: `${index * 30}ms` }}
          >
            <button
              onClick={() => onPivotIntersection(entity.entity_value)}
              className="text-cyan hover:underline font-mono text-sm truncate max-w-[180px]"
              title={`View events where ${currentEntityType}=${currentEntityValue} AND ${entity.entity_type}=${entity.entity_value}`}
            >
              {entity.entity_value}
            </button>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground tabular-nums">
                {entity.count.toLocaleString()} shared
              </span>
              <button
                onClick={() => onPivotIntersection(entity.entity_value)}
                className={cn(
                  "px-2 py-1 rounded text-xs font-medium",
                  "bg-cyan/10 text-cyan border border-cyan/20",
                  "hover:bg-cyan/20 transition-colors"
                )}
                title={`Filter: ${currentEntityType}=${currentEntityValue} AND ${entity.entity_type}=${entity.entity_value}`}
              >
                +Both
              </button>
              <button
                onClick={() => onPivotSingle(entity.entity_value)}
                className={cn(
                  "px-2 py-1 rounded text-xs font-medium",
                  "bg-secondary text-muted-foreground border border-border",
                  "hover:text-foreground hover:border-cyan/30 transition-colors"
                )}
                title={`View ALL events for ${entity.entity_value} only`}
              >
                Only
              </button>
              <button
                onClick={() => onNavigate(entity.entity_value)}
                className={cn(
                  "p-1 rounded text-xs",
                  "bg-secondary text-muted-foreground border border-border",
                  "hover:text-foreground hover:border-cyan/30 transition-colors"
                )}
                title={`View entity details for ${entity.entity_value}`}
                aria-label={`View entity details for ${entity.entity_value}`}
              >
                <Eye className="w-3.5 h-3.5" aria-hidden="true" />
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
