"use client";

import { useState, useCallback, useRef } from "react";
import { useParams, useSearchParams, useRouter } from "next/navigation";
import {
  Clock,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
} from "lucide-react";
import { useEvents } from "@/hooks/useEvents";
import { usePivotStore, getPivotFilterParams } from "@/stores/pivotStore";
import { usePivotContext } from "@/hooks/usePivotContext";
import {
  SeverityBadge,
  getSeverityRowClass,
} from "@/components/common/SeverityBadge";
import { PivotChain } from "@/components/entity/PivotChain";
import { EventDetailModal } from "@/components/timeline/EventDetailModal";
import { formatDate } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type { Event } from "@/lib/types";

// URL param helpers
function useTimelineParams() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const params = useParams();
  const caseId = params.caseId as string;

  const page = parseInt(searchParams.get("page") || "1", 10);
  const pageSize = parseInt(searchParams.get("pageSize") || "50", 10);
  const sortBy = (searchParams.get("sort") as "event_ts" | "-event_ts") || "event_ts";

  const setParams = useCallback(
    (updates: { page?: number; sort?: string }) => {
      const newParams = new URLSearchParams(searchParams.toString());

      if (updates.page !== undefined) {
        if (updates.page === 1) {
          newParams.delete("page");
        } else {
          newParams.set("page", updates.page.toString());
        }
      }

      if (updates.sort !== undefined) {
        if (updates.sort === "event_ts") {
          newParams.delete("sort");
        } else {
          newParams.set("sort", updates.sort);
        }
      }

      const queryString = newParams.toString();
      router.push(
        `/cases/${caseId}/timeline${queryString ? `?${queryString}` : ""}`,
        { scroll: false }
      );
    },
    [searchParams, router, caseId]
  );

  return { page, pageSize, sortBy, setParams, caseId };
}

export default function TimelinePage() {
  const { page, pageSize, sortBy, setParams, caseId } = useTimelineParams();
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  const { pivotEntities } = usePivotStore();
  const { pivotToTimeline, navigateToEntity } = usePivotContext();

  // Memoized handlers for pagination and sorting
  const setPage = useCallback(
    (newPage: number) => setParams({ page: newPage }),
    [setParams]
  );

  const toggleSort = useCallback(
    () => setParams({ sort: sortBy === "event_ts" ? "-event_ts" : "event_ts" }),
    [setParams, sortBy]
  );

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
          <div
            className="inline-block animate-spin rounded-full h-8 w-8 border-2 border-cyan border-t-transparent mb-3"
            role="status"
            aria-label="Loading events"
          />
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
            <Clock className="w-5 h-5 text-cyan" aria-hidden="true" />
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
            onClick={toggleSort}
            className={cn(
              "flex items-center gap-2 px-3 py-2 rounded-lg text-sm",
              "bg-secondary border border-border",
              "hover:border-cyan/30 transition-all duration-200"
            )}
            aria-label={`Sort by ${sortBy === "event_ts" ? "newest" : "oldest"} first`}
          >
            <ArrowUpDown className="w-4 h-4" aria-hidden="true" />
            {sortBy === "event_ts" ? "Oldest First" : "Newest First"}
          </button>
        </div>
      </div>

      {/* Pivot Chain */}
      <PivotChain />

      {/* Events Table */}
      <div className="flex-1 overflow-hidden rounded-xl border border-border glow-border-subtle">
        <div className="overflow-auto h-full scan-lines">
          <table className="data-table" aria-label="Timeline events">
            <caption className="sr-only">
              Security events timeline showing {data?.total ?? 0} events{pivotEntities.length > 0 ? " (filtered)" : ""}
            </caption>
            <thead>
              <tr>
                <th scope="col">Time</th>
                <th scope="col">Source</th>
                <th scope="col">Type</th>
                <th scope="col">Host</th>
                <th scope="col">User</th>
                <th scope="col">Severity</th>
                <th scope="col">Message</th>
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
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      setSelectedEvent(event);
                    }
                  }}
                  tabIndex={0}
                  role="button"
                  aria-label={`Event at ${formatDate(event.event_ts)}: ${event.event_type} - ${event.message || "No message"}`}
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
          closeButtonRef={closeButtonRef}
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
      aria-label={label}
      className={cn(
        "p-2 rounded-lg border border-border",
        "hover:border-cyan/30 hover:bg-secondary",
        "disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:border-border disabled:hover:bg-transparent",
        "transition-all duration-200"
      )}
    >
      <Icon className="w-4 h-4" aria-hidden="true" />
    </button>
  );
}
