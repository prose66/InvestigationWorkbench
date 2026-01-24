"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import {
  LayoutDashboard,
  Activity,
  Database,
  Server,
  Clock,
  Users,
  Network,
  ArrowRight,
  Calendar,
  Layers,
  Shield,
} from "lucide-react";
import { useCaseSummary } from "@/hooks/useCases";
import { PivotChain } from "@/components/entity/PivotChain";
import { formatDate } from "@/lib/utils";
import { cn } from "@/lib/utils";

export default function CaseOverviewPage() {
  const params = useParams();
  const caseId = params.caseId as string;
  const { data: summary, isLoading, error } = useCaseSummary(caseId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-2 border-cyan border-t-transparent mb-3" />
          <p className="text-muted-foreground text-sm">Loading case data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12 metric-card">
        <h2 className="text-xl font-semibold text-destructive mb-2">Error</h2>
        <p className="text-muted-foreground">Failed to load case summary</p>
      </div>
    );
  }

  if (!summary) return null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-cyan/10 pulse-glow">
          <LayoutDashboard className="w-5 h-5 text-cyan" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-foreground">Case Overview</h1>
          <p className="text-muted-foreground text-sm font-mono">{caseId}</p>
        </div>
      </div>

      {/* Pivot Chain */}
      <PivotChain />

      {/* Metrics Grid */}
      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard
          icon={Activity}
          label="Total Events"
          value={summary.total_events.toLocaleString()}
          highlight
        />
        <MetricCard
          icon={Layers}
          label="Query Runs"
          value={summary.total_runs.toString()}
        />
        <MetricCard
          icon={Database}
          label="Sources"
          value={summary.total_sources.toString()}
        />
        <MetricCard
          icon={Server}
          label="Unique Hosts"
          value={summary.total_hosts.toString()}
        />
      </div>

      {/* Time Coverage */}
      {summary.min_ts && summary.max_ts && (
        <div
          className={cn(
            "relative overflow-hidden rounded-xl p-4",
            "bg-gradient-to-r from-cyan/10 via-background to-background",
            "border border-cyan/20"
          )}
        >
          <div className="absolute top-0 left-0 w-1 h-full bg-cyan" />
          <div className="flex items-center gap-3 pl-2">
            <Calendar className="w-4 h-4 text-cyan" />
            <div>
              <p className="text-xs text-muted-foreground uppercase tracking-wider font-medium mb-1">
                Time Coverage
              </p>
              <p className="text-foreground font-mono text-sm">
                {formatDate(summary.min_ts)}{" "}
                <span className="text-muted-foreground mx-2">to</span>{" "}
                {formatDate(summary.max_ts)}{" "}
                <span className="text-muted-foreground">(UTC)</span>
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Quick Links */}
      <div className="grid gap-4 md:grid-cols-3">
        <QuickLink
          href={`/cases/${caseId}/timeline`}
          icon={Clock}
          title="Timeline Explorer"
          description="View and filter events chronologically"
        />
        <QuickLink
          href={`/cases/${caseId}/entity`}
          icon={Users}
          title="Entity Analysis"
          description="Explore hosts, users, IPs, and more"
        />
        <QuickLink
          href={`/cases/${caseId}/graph`}
          icon={Network}
          title="Entity Graph"
          description="Visualize entity relationships"
        />
      </div>

      {/* Source Systems & Event Types */}
      <div className="grid gap-6 md:grid-cols-2">
        <div className="metric-card">
          <div className="flex items-center gap-2 mb-4">
            <Database className="w-4 h-4 text-cyan" />
            <h3 className="font-semibold text-foreground">Source Systems</h3>
          </div>
          <ul className="space-y-2">
            {summary.source_systems.map((source, index) => (
              <li
                key={source}
                className={cn(
                  "flex items-center gap-2 text-sm p-2 rounded-lg",
                  "bg-secondary/30 border border-border/30",
                  "fade-in-up"
                )}
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <div className="w-2 h-2 rounded-full bg-cyan/50" />
                <span className="font-mono text-foreground">{source}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="metric-card">
          <div className="flex items-center gap-2 mb-4">
            <Shield className="w-4 h-4 text-cyan" />
            <h3 className="font-semibold text-foreground">Event Types</h3>
            {summary.event_types.length > 10 && (
              <span className="text-xs text-muted-foreground">
                (showing 10 of {summary.event_types.length})
              </span>
            )}
          </div>
          <ul className="space-y-2">
            {summary.event_types.slice(0, 10).map((type, index) => (
              <li
                key={type}
                className={cn(
                  "flex items-center gap-2 text-sm p-2 rounded-lg",
                  "bg-secondary/30 border border-border/30",
                  "fade-in-up"
                )}
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <div className="w-2 h-2 rounded-full bg-amber-400/50" />
                <span className="text-muted-foreground">{type}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

function MetricCard({
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
    <div className="metric-card fade-in-up">
      <div className="flex items-center gap-2 mb-2">
        <Icon
          className={cn(
            "w-4 h-4",
            highlight ? "text-cyan" : "text-muted-foreground"
          )}
        />
        <p className="text-xs text-muted-foreground uppercase tracking-wider font-medium">
          {label}
        </p>
      </div>
      <p
        className={cn(
          "text-2xl font-bold",
          highlight ? "text-cyan" : "text-foreground"
        )}
      >
        {value}
      </p>
    </div>
  );
}

function QuickLink({
  href,
  icon: Icon,
  title,
  description,
}: {
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
}) {
  return (
    <Link
      href={href}
      className={cn(
        "group relative overflow-hidden rounded-xl p-5",
        "card-gradient border border-border",
        "hover:border-cyan/30 hover:glow-border-subtle",
        "transition-all duration-300",
        "fade-in-up"
      )}
    >
      {/* Top accent */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-border to-transparent group-hover:via-cyan/50 transition-all duration-300" />

      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-secondary group-hover:bg-cyan/10 transition-colors duration-300">
            <Icon className="w-5 h-5 text-muted-foreground group-hover:text-cyan transition-colors duration-300" />
          </div>
          <div>
            <h4 className="font-semibold text-foreground group-hover:text-cyan transition-colors duration-300">
              {title}
            </h4>
            <p className="text-sm text-muted-foreground mt-1">{description}</p>
          </div>
        </div>
        <ArrowRight className="w-5 h-5 text-muted-foreground group-hover:text-cyan group-hover:translate-x-1 transition-all duration-300" />
      </div>
    </Link>
  );
}
