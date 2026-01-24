"use client";

import { cn } from "@/lib/utils";
import { AlertTriangle, AlertCircle, Info, CheckCircle } from "lucide-react";

interface SeverityBadgeProps {
  severity?: string;
  className?: string;
  showIcon?: boolean;
}

const severityConfig = {
  critical: {
    className: "badge-critical",
    icon: AlertTriangle,
    pulse: true,
  },
  high: {
    className: "badge-high",
    icon: AlertCircle,
    pulse: false,
  },
  medium: {
    className: "badge-medium",
    icon: AlertTriangle,
    pulse: false,
  },
  low: {
    className: "badge-low",
    icon: CheckCircle,
    pulse: false,
  },
  info: {
    className: "badge-info",
    icon: Info,
    pulse: false,
  },
};

export function SeverityBadge({
  severity,
  className,
  showIcon = true,
}: SeverityBadgeProps) {
  if (!severity) return null;

  const normalizedSeverity = severity.toLowerCase();
  const config =
    severityConfig[normalizedSeverity as keyof typeof severityConfig] ||
    severityConfig.info;

  const Icon = config.icon;

  return (
    <span
      className={cn(
        "badge",
        config.className,
        config.pulse && "animate-pulse",
        className
      )}
    >
      {showIcon && <Icon className="w-3 h-3 mr-1" />}
      <span className="uppercase tracking-wider font-semibold">{severity}</span>
    </span>
  );
}

// Row highlight component for data tables
export function getSeverityRowClass(severity?: string): string {
  if (!severity) return "";

  const normalizedSeverity = severity.toLowerCase();
  switch (normalizedSeverity) {
    case "critical":
      return "severity-critical-row";
    case "high":
      return "severity-high-row";
    case "medium":
      return "severity-medium-row";
    case "low":
      return "severity-low-row";
    default:
      return "";
  }
}
