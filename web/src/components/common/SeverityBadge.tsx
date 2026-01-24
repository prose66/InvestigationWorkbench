import { cn } from "@/lib/utils";

interface SeverityBadgeProps {
  severity?: string;
  className?: string;
}

export function SeverityBadge({ severity, className }: SeverityBadgeProps) {
  if (!severity) return null;

  const colorClass = {
    high: "bg-red-100 text-red-800 border-red-200",
    critical: "bg-red-100 text-red-800 border-red-200",
    medium: "bg-orange-100 text-orange-800 border-orange-200",
    low: "bg-green-100 text-green-800 border-green-200",
  }[severity.toLowerCase()] || "bg-gray-100 text-gray-800 border-gray-200";

  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border",
        colorClass,
        className
      )}
    >
      {severity}
    </span>
  );
}
