"use client";

import { FileJson, X, Loader2, CheckCircle, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { FileEntry } from "@/lib/types";

interface FileCardProps {
  entry: FileEntry;
  index: number;
  onRemove: () => void;
  onSourceChange: (source: string) => void;
  onQueryNameChange: (queryName: string) => void;
}

export function FileCard({
  entry,
  index,
  onRemove,
  onSourceChange,
  onQueryNameChange,
}: FileCardProps) {
  const hasPreview = entry.previewData !== null;
  const isValid = entry.source.trim() && entry.queryName.trim();

  return (
    <div
      className={cn(
        "metric-card p-4 border-2 transition-colors",
        entry.error
          ? "border-destructive/50"
          : hasPreview
          ? "border-emerald-500/50"
          : isValid
          ? "border-cyan/30"
          : "border-border"
      )}
    >
      <div className="flex items-start gap-3">
        {/* File icon with status */}
        <div
          className={cn(
            "flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center",
            entry.error
              ? "bg-destructive/10"
              : hasPreview
              ? "bg-emerald-500/10"
              : "bg-cyan/10"
          )}
        >
          {entry.isLoading ? (
            <Loader2 className="w-5 h-5 text-cyan animate-spin" />
          ) : entry.error ? (
            <AlertCircle className="w-5 h-5 text-destructive" />
          ) : hasPreview ? (
            <CheckCircle className="w-5 h-5 text-emerald-500" />
          ) : (
            <FileJson className="w-5 h-5 text-cyan" />
          )}
        </div>

        {/* File info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs text-muted-foreground">#{index + 1}</span>
            <span
              className="font-medium text-foreground truncate"
              title={entry.file.name}
            >
              {entry.file.name}
            </span>
            <span className="text-xs text-muted-foreground">
              ({(entry.file.size / 1024).toFixed(1)} KB)
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">
                Source System <span className="text-destructive">*</span>
              </label>
              <input
                type="text"
                value={entry.source}
                onChange={(e) => onSourceChange(e.target.value)}
                placeholder="e.g., splunk"
                className="w-full px-2 py-1.5 bg-secondary/50 border border-border rounded text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-cyan/50"
              />
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">
                Query Name <span className="text-destructive">*</span>
              </label>
              <input
                type="text"
                value={entry.queryName}
                onChange={(e) => onQueryNameChange(e.target.value)}
                placeholder="e.g., Jan 2024 logins"
                className="w-full px-2 py-1.5 bg-secondary/50 border border-border rounded text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-cyan/50"
              />
            </div>
          </div>

          {/* Preview info */}
          {hasPreview && entry.previewData && (
            <div className="mt-2 flex items-center gap-4 text-xs text-muted-foreground">
              <span>
                <span className="text-foreground font-medium">
                  {entry.previewData.total_rows.toLocaleString()}
                </span>{" "}
                rows
              </span>
              <span>
                <span className="text-foreground font-medium">
                  {entry.previewData.source_fields.length}
                </span>{" "}
                fields
              </span>
              <span className="uppercase">{entry.previewData.file_format}</span>
            </div>
          )}

          {/* Error message */}
          {entry.error && (
            <p className="mt-2 text-xs text-destructive">{entry.error}</p>
          )}
        </div>

        {/* Remove button */}
        <button
          onClick={onRemove}
          className="flex-shrink-0 p-1 text-muted-foreground hover:text-destructive transition-colors"
          title="Remove file"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
