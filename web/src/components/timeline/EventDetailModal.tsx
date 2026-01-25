"use client";

import { memo, useRef, useEffect } from "react";
import {
  Eye,
  X,
  Filter,
  ExternalLink,
  Terminal,
} from "lucide-react";
import { SeverityBadge } from "@/components/common/SeverityBadge";
import { formatDate } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type { Event } from "@/lib/types";

interface EventDetailModalProps {
  event: Event;
  onClose: () => void;
  onPivot: (type: string, value: string) => void;
  onNavigate: (type: string, value: string) => void;
  closeButtonRef?: React.RefObject<HTMLButtonElement>;
}

export const EventDetailModal = memo(function EventDetailModal({
  event,
  onClose,
  onPivot,
  onNavigate,
  closeButtonRef,
}: EventDetailModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);

  // Focus trap and keyboard handling
  useEffect(() => {
    const modal = modalRef.current;
    if (!modal) return;

    // Focus the close button when modal opens
    closeButtonRef?.current?.focus();

    // Handle escape key
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
      // Focus trap
      if (e.key === "Tab") {
        const focusableElements = modal.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (e.shiftKey && document.activeElement === firstElement) {
          e.preventDefault();
          lastElement?.focus();
        } else if (!e.shiftKey && document.activeElement === lastElement) {
          e.preventDefault();
          firstElement?.focus();
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose, closeButtonRef]);

  return (
    <div
      className="modal-backdrop"
      onClick={onClose}
      role="presentation"
    >
      <div
        ref={modalRef}
        className="modal-content max-w-2xl w-full max-h-[85vh] overflow-hidden m-4 fade-in-up"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="event-modal-title"
      >
        {/* Header */}
        <div className="sticky top-0 bg-card border-b border-border px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-1.5 rounded-lg bg-cyan/10">
              <Eye className="w-4 h-4 text-cyan" aria-hidden="true" />
            </div>
            <h2 id="event-modal-title" className="font-semibold text-foreground">Event Details</h2>
          </div>
          <button
            ref={closeButtonRef as React.RefObject<HTMLButtonElement>}
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" aria-hidden="true" />
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
                <Terminal className="w-3 h-3 text-muted-foreground" aria-hidden="true" />
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
});

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
      {variant === "primary" && <Filter className="w-3 h-3" aria-hidden="true" />}
      {variant === "secondary" && <ExternalLink className="w-3 h-3" aria-hidden="true" />}
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
