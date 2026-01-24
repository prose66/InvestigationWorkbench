"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import {
  Clock,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  X,
  Eye,
  Filter,
  Zap,
  Terminal,
  ExternalLink,
} from "lucide-react";
import { useEvents } from "@/hooks/useEvents";
import { usePivotStore, getPivotFilterParams } from "@/stores/pivotStore";
import { usePivotContext } from "@/hooks/usePivotContext";
import {
  SeverityBadge,
  getSeverityRowClass,
} from "@/components/common/SeverityBadge";
import { PivotChain } from "@/components/entity/PivotChain";
import { formatDate, truncate } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type { Event } from "@/lib/types";

export default function TimelinePage() {
  const params = useParams();
  const caseId = params.caseId as string;
  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);
  const [sortBy, setSortBy] = useState<"event_ts" | "-event_ts">("event_ts");
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);

  const { pivotEntities } = usePivotStore();
  const { pivotToTimeline, navigateToEntity } = usePivotContext();

  // Build filter params from pivot entities
  const pivotFilters = getPivotFilterParams(pivotEntities);

  const { data, isLoading, error } = useEvents(caseId, {
    ...pivotFilters,
    page,
    page_size: pageSize,
    sort_by: sortBy,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-2 border-cyan border-t-transparent mb-3" />
          <p className="text-muted-foreground text-sm">Loading events...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12 metric-card">
        <h2 className="text-xl font-semibold text-destructive mb-2">Error</h2>
        <p className="text-muted-foreground">Failed to load events</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-cyan/10 pulse-glow">
            <Clock className="w-5 h-5 text-cyan" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-foreground">
              Timeline Explorer
            </h1>
            <p className="text-muted-foreground text-sm">
              <span className="text-cyan font-semibold">
                {data?.total.toLocaleString() ?? 0}
              </span>{" "}
              events
              {pivotEntities.length > 0 && " (filtered)"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() =>
              setSortBy(sortBy === "event_ts" ? "-event_ts" : "event_ts")
            }
            className={cn(
              "flex items-center gap-2 px-3 py-2 rounded-lg text-sm",
              "bg-secondary border border-border",
              "hover:border-cyan/30 transition-all duration-200"
            )}
          >
            <ArrowUpDown className="w-4 h-4" />
            {sortBy === "event_ts" ? "Oldest First" : "Newest First"}
          </button>
        </div>
      </div>

      {/* Pivot Chain */}
      <PivotChain />

      {/* Events Table */}
      <div className="flex-1 overflow-hidden rounded-xl border border-border glow-border-subtle">
        <div className="overflow-auto h-full scan-lines">
          <table className="data-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Source</th>
                <th>Type</th>
                <th>Host</th>
                <th>User</th>
                <th>Severity</th>
                <th>Message</th>
              </tr>
            </thead>
            <tbody>
              {data?.events.map((event, index) => (
                <tr
                  key={event.event_pk}
                  className={cn(
                    getSeverityRowClass(event.severity),
                    "fade-in-up"
                  )}
                  style={{ animationDelay: `${Math.min(index, 10) * 20}ms` }}
                  onClick={() => setSelectedEvent(event)}
                >
                  <td className="whitespace-nowrap font-mono text-xs">
                    {formatDate(event.event_ts)}
                  </td>
                  <td>
                    <span className="px-2 py-0.5 rounded bg-secondary text-xs font-medium">
                      {event.source_system}
                    </span>
                  </td>
                  <td className="text-muted-foreground">{event.event_type}</td>
                  <td>
                    {event.host && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          pivotToTimeline("host", event.host!);
                        }}
                        className="text-cyan hover:underline font-mono text-sm"
                      >
                        {event.host}
                      </button>
                    )}
                  </td>
                  <td>
                    {event.user && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          pivotToTimeline("user", event.user!);
                        }}
                        className="text-cyan hover:underline font-mono text-sm"
                      >
                        {event.user}
                      </button>
                    )}
                  </td>
                  <td>
                    <SeverityBadge severity={event.severity} showIcon={false} />
                  </td>
                  <td className="max-w-xs truncate text-muted-foreground">
                    {event.message}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between py-2">
        <div className="text-sm text-muted-foreground">
          Page{" "}
          <span className="text-foreground font-medium">{data?.page ?? 1}</span>{" "}
          of{" "}
          <span className="text-foreground font-medium">
            {data?.total_pages ?? 1}
          </span>
        </div>
        <div className="flex gap-1">
          <PaginationButton
            onClick={() => setPage(1)}
            disabled={page === 1}
            icon={ChevronsLeft}
            label="First"
          />
          <PaginationButton
            onClick={() => setPage(page - 1)}
            disabled={page === 1}
            icon={ChevronLeft}
            label="Previous"
          />
          <PaginationButton
            onClick={() => setPage(page + 1)}
            disabled={page >= (data?.total_pages ?? 1)}
            icon={ChevronRight}
            label="Next"
          />
          <PaginationButton
            onClick={() => setPage(data?.total_pages ?? 1)}
            disabled={page >= (data?.total_pages ?? 1)}
            icon={ChevronsRight}
            label="Last"
          />
        </div>
      </div>

      {/* Event Detail Modal */}
      {selectedEvent && (
        <EventDetailModal
          event={selectedEvent}
          onClose={() => setSelectedEvent(null)}
          onPivot={(type, value) => {
            pivotToTimeline(type, value);
            setSelectedEvent(null);
          }}
          onNavigate={(type, value) => {
            navigateToEntity(type, value);
            setSelectedEvent(null);
          }}
        />
      )}
    </div>
  );
}

function PaginationButton({
  onClick,
  disabled,
  icon: Icon,
  label,
}: {
  onClick: () => void;
  disabled: boolean;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={label}
      className={cn(
        "p-2 rounded-lg border border-border",
        "hover:border-cyan/30 hover:bg-secondary",
        "disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:border-border disabled:hover:bg-transparent",
        "transition-all duration-200"
      )}
    >
      <Icon className="w-4 h-4" />
    </button>
  );
}

function EventDetailModal({
  event,
  onClose,
  onPivot,
  onNavigate,
}: {
  event: Event;
  onClose: () => void;
  onPivot: (type: string, value: string) => void;
  onNavigate: (type: string, value: string) => void;
}) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-content max-w-2xl w-full max-h-[85vh] overflow-hidden m-4 fade-in-up"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-card border-b border-border px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-1.5 rounded-lg bg-cyan/10">
              <Eye className="w-4 h-4 text-cyan" />
            </div>
            <h2 className="font-semibold text-foreground">Event Details</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-5 overflow-auto max-h-[calc(85vh-60px)]">
          {/* Quick Pivots */}
          <div className="flex flex-wrap gap-2">
            {event.host && (
              <>
                <QuickPivotButton
                  label={`+Filter: ${event.host}`}
                  onClick={() => onPivot("host", event.host!)}
                  variant="primary"
                />
                <QuickPivotButton
                  label="View Host"
                  onClick={() => onNavigate("host", event.host!)}
                  variant="secondary"
                />
              </>
            )}
            {event.user && (
              <>
                <QuickPivotButton
                  label={`+Filter: ${event.user}`}
                  onClick={() => onPivot("user", event.user!)}
                  variant="primary"
                />
                <QuickPivotButton
                  label="View User"
                  onClick={() => onNavigate("user", event.user!)}
                  variant="secondary"
                />
              </>
            )}
            {event.src_ip && (
              <QuickPivotButton
                label={`+Filter: ${event.src_ip}`}
                onClick={() => onPivot("ip", event.src_ip!)}
                variant="primary"
              />
            )}
          </div>

          {/* Event Info Grid */}
          <div className="grid grid-cols-2 gap-4">
            <InfoField label="Time" value={formatDate(event.event_ts)} mono />
            <InfoField label="Source System" value={event.source_system} />
            <InfoField label="Event Type" value={event.event_type} />
            <InfoField
              label="Severity"
              value={<SeverityBadge severity={event.severity} />}
            />
            {event.host && <InfoField label="Host" value={event.host} mono />}
            {event.user && <InfoField label="User" value={event.user} mono />}
            {event.src_ip && (
              <InfoField label="Source IP" value={event.src_ip} mono />
            )}
            {event.dest_ip && (
              <InfoField label="Dest IP" value={event.dest_ip} mono />
            )}
            {event.process_name && (
              <InfoField label="Process" value={event.process_name} mono />
            )}
            {event.tactic && (
              <InfoField label="MITRE Tactic" value={event.tactic} />
            )}
            {event.technique && (
              <InfoField label="MITRE Technique" value={event.technique} />
            )}
          </div>

          {/* Message */}
          {event.message && (
            <div>
              <p className="text-xs text-muted-foreground uppercase tracking-wider font-medium mb-2">
                Message
              </p>
              <div className="bg-secondary/50 border border-border rounded-lg p-4 text-sm">
                {event.message}
              </div>
            </div>
          )}

          {/* Process Details */}
          {event.process_cmdline && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Terminal className="w-3 h-3 text-muted-foreground" />
                <p className="text-xs text-muted-foreground uppercase tracking-wider font-medium">
                  Command Line
                </p>
              </div>
              <pre className="bg-background border border-border rounded-lg p-4 text-sm font-mono break-all whitespace-pre-wrap overflow-x-auto">
                {event.process_cmdline}
              </pre>
            </div>
          )}

          {/* Raw JSON */}
          {event.raw_json && (
            <div>
              <p className="text-xs text-muted-foreground uppercase tracking-wider font-medium mb-2">
                Raw JSON
              </p>
              <pre className="bg-background border border-border rounded-lg p-4 text-xs font-mono overflow-auto max-h-48">
                {JSON.stringify(event.raw_json, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function QuickPivotButton({
  label,
  onClick,
  variant,
}: {
  label: string;
  onClick: () => void;
  variant: "primary" | "secondary";
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium",
        "transition-all duration-200",
        variant === "primary"
          ? "bg-cyan/15 text-cyan border border-cyan/30 hover:bg-cyan/25"
          : "bg-secondary text-muted-foreground border border-border hover:text-foreground hover:border-cyan/30"
      )}
    >
      {variant === "primary" && <Filter className="w-3 h-3" />}
      {variant === "secondary" && <ExternalLink className="w-3 h-3" />}
      {label}
    </button>
  );
}

function InfoField({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: React.ReactNode;
  mono?: boolean;
}) {
  return (
    <div>
      <p className="text-xs text-muted-foreground uppercase tracking-wider font-medium mb-1">
        {label}
      </p>
      <p className={cn("text-sm text-foreground", mono && "font-mono")}>
        {value}
      </p>
    </div>
  );
}
