import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return d.toLocaleString();
}

export function formatShortDate(date: string | Date): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return d.toLocaleDateString();
}

export function getSeverityColor(severity?: string): string {
  switch (severity?.toLowerCase()) {
    case "high":
    case "critical":
      return "text-severity-high";
    case "medium":
      return "text-severity-medium";
    case "low":
      return "text-severity-low";
    default:
      return "text-muted-foreground";
  }
}

export function getSeverityBgColor(severity?: string): string {
  switch (severity?.toLowerCase()) {
    case "high":
    case "critical":
      return "bg-red-100 border-red-300";
    case "medium":
      return "bg-orange-100 border-orange-300";
    case "low":
      return "bg-green-100 border-green-300";
    default:
      return "bg-muted";
  }
}

export function truncate(str: string, length: number): string {
  if (str.length <= length) return str;
  return str.slice(0, length) + "...";
}
