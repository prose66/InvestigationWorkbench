"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useCaseSummary } from "@/hooks/useCases";
import { formatDate } from "@/lib/utils";

export default function CaseOverviewPage() {
  const params = useParams();
  const caseId = params.caseId as string;
  const { data: summary, isLoading, error } = useCaseSummary(caseId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-destructive mb-2">Error</h2>
        <p className="text-muted-foreground">Failed to load case summary</p>
      </div>
    );
  }

  if (!summary) return null;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Case Overview</h1>
      <p className="text-muted-foreground mb-6">Case: {caseId}</p>

      {/* Metrics */}
      <div className="grid gap-4 md:grid-cols-4 mb-8">
        <MetricCard label="Total Events" value={summary.total_events.toLocaleString()} />
        <MetricCard label="Query Runs" value={summary.total_runs.toString()} />
        <MetricCard label="Sources" value={summary.total_sources.toString()} />
        <MetricCard label="Unique Hosts" value={summary.total_hosts.toString()} />
      </div>

      {/* Time Coverage */}
      {summary.min_ts && summary.max_ts && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-8">
          <p className="text-blue-800">
            <strong>Time Coverage:</strong> {formatDate(summary.min_ts)} to{" "}
            {formatDate(summary.max_ts)} (UTC)
          </p>
        </div>
      )}

      {/* Quick Links */}
      <div className="grid gap-4 md:grid-cols-3 mb-8">
        <QuickLink
          href={`/cases/${caseId}/timeline`}
          title="Timeline Explorer"
          description="View and filter events chronologically"
        />
        <QuickLink
          href={`/cases/${caseId}/entity`}
          title="Entity Analysis"
          description="Explore hosts, users, IPs, and more"
        />
        <QuickLink
          href={`/cases/${caseId}/graph`}
          title="Entity Graph"
          description="Visualize entity relationships"
        />
      </div>

      {/* Source Systems */}
      <div className="grid gap-6 md:grid-cols-2">
        <div className="bg-card border rounded-lg p-4">
          <h3 className="font-semibold mb-3">Source Systems</h3>
          <ul className="space-y-2">
            {summary.source_systems.map((source) => (
              <li key={source} className="text-sm text-muted-foreground">
                {source}
              </li>
            ))}
          </ul>
        </div>

        <div className="bg-card border rounded-lg p-4">
          <h3 className="font-semibold mb-3">Event Types</h3>
          <ul className="space-y-2">
            {summary.event_types.slice(0, 10).map((type) => (
              <li key={type} className="text-sm text-muted-foreground">
                {type}
              </li>
            ))}
            {summary.event_types.length > 10 && (
              <li className="text-sm text-muted-foreground">
                +{summary.event_types.length - 10} more
              </li>
            )}
          </ul>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-card border rounded-lg p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
}

function QuickLink({
  href,
  title,
  description,
}: {
  href: string;
  title: string;
  description: string;
}) {
  return (
    <Link
      href={href}
      className="block bg-card border rounded-lg p-4 hover:shadow-md transition-shadow"
    >
      <h4 className="font-semibold">{title}</h4>
      <p className="text-sm text-muted-foreground mt-1">{description}</p>
    </Link>
  );
}
