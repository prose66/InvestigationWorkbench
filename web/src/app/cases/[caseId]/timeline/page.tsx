"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useEvents } from "@/hooks/useEvents";
import { usePivotStore, getPivotFilterParams } from "@/stores/pivotStore";
import { usePivotContext } from "@/hooks/usePivotContext";
import { SeverityBadge } from "@/components/common/SeverityBadge";
import { formatDate, truncate } from "@/lib/utils";
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
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-destructive mb-2">Error</h2>
        <p className="text-muted-foreground">Failed to load events</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold">Timeline Explorer</h1>
          <p className="text-muted-foreground text-sm">
            {data?.total.toLocaleString() ?? 0} events
          </p>
        </div>

        <div className="flex items-center gap-4">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
            className="px-3 py-2 border rounded-md bg-background text-sm"
          >
            <option value="event_ts">Oldest First</option>
            <option value="-event_ts">Newest First</option>
          </select>
        </div>
      </div>

      {/* Events Table */}
      <div className="flex-1 overflow-auto border rounded-lg">
        <table className="w-full text-sm">
          <thead className="bg-muted sticky top-0">
            <tr>
              <th className="px-4 py-3 text-left">Time</th>
              <th className="px-4 py-3 text-left">Source</th>
              <th className="px-4 py-3 text-left">Type</th>
              <th className="px-4 py-3 text-left">Host</th>
              <th className="px-4 py-3 text-left">User</th>
              <th className="px-4 py-3 text-left">Severity</th>
              <th className="px-4 py-3 text-left">Message</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {data?.events.map((event) => (
              <tr
                key={event.event_pk}
                className="hover:bg-muted/50 cursor-pointer"
                onClick={() => setSelectedEvent(event)}
              >
                <td className="px-4 py-2 whitespace-nowrap">
                  {formatDate(event.event_ts)}
                </td>
                <td className="px-4 py-2">{event.source_system}</td>
                <td className="px-4 py-2">{event.event_type}</td>
                <td className="px-4 py-2">
                  {event.host && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        pivotToTimeline("host", event.host!);
                      }}
                      className="text-blue-600 hover:underline"
                    >
                      {event.host}
                    </button>
                  )}
                </td>
                <td className="px-4 py-2">
                  {event.user && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        pivotToTimeline("user", event.user!);
                      }}
                      className="text-blue-600 hover:underline"
                    >
                      {event.user}
                    </button>
                  )}
                </td>
                <td className="px-4 py-2">
                  <SeverityBadge severity={event.severity} />
                </td>
                <td className="px-4 py-2 max-w-xs truncate">
                  {event.message}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between mt-4">
        <div className="text-sm text-muted-foreground">
          Page {data?.page ?? 1} of {data?.total_pages ?? 1}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setPage(1)}
            disabled={page === 1}
            className="px-3 py-1 border rounded text-sm disabled:opacity-50"
          >
            First
          </button>
          <button
            onClick={() => setPage(page - 1)}
            disabled={page === 1}
            className="px-3 py-1 border rounded text-sm disabled:opacity-50"
          >
            Prev
          </button>
          <button
            onClick={() => setPage(page + 1)}
            disabled={page >= (data?.total_pages ?? 1)}
            className="px-3 py-1 border rounded text-sm disabled:opacity-50"
          >
            Next
          </button>
          <button
            onClick={() => setPage(data?.total_pages ?? 1)}
            disabled={page >= (data?.total_pages ?? 1)}
            className="px-3 py-1 border rounded text-sm disabled:opacity-50"
          >
            Last
          </button>
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
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-card rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-auto m-4">
        <div className="sticky top-0 bg-card border-b px-6 py-4 flex items-center justify-between">
          <h2 className="font-semibold">Event Details</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            Close
          </button>
        </div>

        <div className="p-6 space-y-4">
          {/* Quick Pivots */}
          <div className="flex flex-wrap gap-2">
            {event.host && (
              <>
                <button
                  onClick={() => onPivot("host", event.host!)}
                  className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs"
                >
                  +Filter: {event.host}
                </button>
                <button
                  onClick={() => onNavigate("host", event.host!)}
                  className="px-2 py-1 bg-gray-100 rounded text-xs"
                >
                  View Host
                </button>
              </>
            )}
            {event.user && (
              <>
                <button
                  onClick={() => onPivot("user", event.user!)}
                  className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs"
                >
                  +Filter: {event.user}
                </button>
                <button
                  onClick={() => onNavigate("user", event.user!)}
                  className="px-2 py-1 bg-gray-100 rounded text-xs"
                >
                  View User
                </button>
              </>
            )}
            {event.src_ip && (
              <button
                onClick={() => onPivot("ip", event.src_ip!)}
                className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs"
              >
                +Filter: {event.src_ip}
              </button>
            )}
          </div>

          {/* Event Info */}
          <dl className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <dt className="text-muted-foreground">Time</dt>
              <dd>{formatDate(event.event_ts)}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Source System</dt>
              <dd>{event.source_system}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Event Type</dt>
              <dd>{event.event_type}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Severity</dt>
              <dd>
                <SeverityBadge severity={event.severity} />
              </dd>
            </div>
            {event.host && (
              <div>
                <dt className="text-muted-foreground">Host</dt>
                <dd>{event.host}</dd>
              </div>
            )}
            {event.user && (
              <div>
                <dt className="text-muted-foreground">User</dt>
                <dd>{event.user}</dd>
              </div>
            )}
            {event.src_ip && (
              <div>
                <dt className="text-muted-foreground">Source IP</dt>
                <dd>{event.src_ip}</dd>
              </div>
            )}
            {event.dest_ip && (
              <div>
                <dt className="text-muted-foreground">Dest IP</dt>
                <dd>{event.dest_ip}</dd>
              </div>
            )}
            {event.process_name && (
              <div>
                <dt className="text-muted-foreground">Process</dt>
                <dd>{event.process_name}</dd>
              </div>
            )}
            {event.tactic && (
              <div>
                <dt className="text-muted-foreground">MITRE Tactic</dt>
                <dd>{event.tactic}</dd>
              </div>
            )}
            {event.technique && (
              <div>
                <dt className="text-muted-foreground">MITRE Technique</dt>
                <dd>{event.technique}</dd>
              </div>
            )}
          </dl>

          {/* Message */}
          {event.message && (
            <div>
              <dt className="text-muted-foreground text-sm mb-1">Message</dt>
              <dd className="bg-muted p-3 rounded text-sm">{event.message}</dd>
            </div>
          )}

          {/* Process Details */}
          {event.process_cmdline && (
            <div>
              <dt className="text-muted-foreground text-sm mb-1">Command Line</dt>
              <dd className="bg-muted p-3 rounded text-sm font-mono break-all">
                {event.process_cmdline}
              </dd>
            </div>
          )}

          {/* Raw JSON */}
          {event.raw_json && (
            <div>
              <dt className="text-muted-foreground text-sm mb-1">Raw JSON</dt>
              <pre className="bg-muted p-3 rounded text-xs overflow-auto max-h-64">
                {JSON.stringify(event.raw_json, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
