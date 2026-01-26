"use client";

import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  Loader2,
  Database,
  ArrowRight,
  FileJson,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useIngestStore } from "@/stores/ingestStore";

interface IngestProgressProps {
  onViewTimeline?: () => void;
  onIngestAnother?: () => void;
}

export function IngestProgress({
  onViewTimeline,
  onIngestAnother,
}: IngestProgressProps) {
  const {
    files,
    results,
    isIngesting,
    ingestError,
    currentIngestIndex,
    getTotalIngested,
    getTotalSkipped,
  } = useIngestStore();

  // Ingesting state
  if (isIngesting) {
    const currentFile = files[currentIngestIndex];
    const completedCount = Object.keys(results).length;

    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Loader2 className="w-12 h-12 text-cyan animate-spin mb-4" />
        <h3 className="text-lg font-semibold text-foreground mb-2">
          Ingesting Files
        </h3>
        <p className="text-sm text-muted-foreground mb-4">
          Processing {currentFile?.file.name || "file"}...
        </p>
        <div className="w-64 h-2 bg-secondary rounded-full overflow-hidden">
          <div
            className="h-full bg-cyan transition-all duration-300"
            style={{
              width: `${((completedCount + 0.5) / files.length) * 100}%`,
            }}
          />
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          {completedCount} of {files.length} files complete
        </p>
      </div>
    );
  }

  // Error state
  if (ingestError) {
    return (
      <div className="metric-card">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 rounded-full bg-destructive/10">
            <XCircle className="w-6 h-6 text-destructive" />
          </div>
          <div>
            <h3 className="font-semibold text-destructive">Ingestion Failed</h3>
            <p className="text-sm text-muted-foreground">{ingestError}</p>
          </div>
        </div>
        {onIngestAnother && (
          <button
            onClick={onIngestAnother}
            className="w-full mt-4 px-4 py-2 bg-secondary hover:bg-secondary/80 text-foreground rounded-lg transition-colors"
          >
            Try Again
          </button>
        )}
      </div>
    );
  }

  // No results yet
  if (Object.keys(results).length === 0) {
    return null;
  }

  // Calculate totals
  const totalIngested = getTotalIngested();
  const totalSkipped = getTotalSkipped();
  const hasErrors = files.some((f) => results[f.id]?.errors.length > 0);
  const allSucceeded = files.every(
    (f) => results[f.id] && results[f.id].errors.length === 0
  );
  const anyMapperSaved = Object.values(results).some((r) => r.mapper_saved);

  return (
    <div className="space-y-6">
      {/* Success header */}
      <div className="flex items-center gap-3">
        <div
          className={cn(
            "p-3 rounded-full",
            hasErrors ? "bg-amber-500/10" : "bg-emerald-500/10"
          )}
        >
          {hasErrors ? (
            <AlertTriangle className="w-8 h-8 text-amber-500" />
          ) : (
            <CheckCircle className="w-8 h-8 text-emerald-500" />
          )}
        </div>
        <div>
          <h2 className="text-xl font-bold text-foreground">
            {hasErrors
              ? "Batch Ingestion Completed with Warnings"
              : "Batch Ingestion Complete"}
          </h2>
          <p className="text-muted-foreground">
            {files.length} file{files.length !== 1 && "s"} processed
          </p>
        </div>
      </div>

      {/* Totals */}
      <div className="grid grid-cols-3 gap-4">
        <div className="metric-card text-center">
          <Database className="w-5 h-5 text-cyan mx-auto mb-2" />
          <p className="text-2xl font-bold text-cyan">
            {totalIngested.toLocaleString()}
          </p>
          <p className="text-xs text-muted-foreground">Total Events Ingested</p>
        </div>
        <div className="metric-card text-center">
          <AlertTriangle
            className={cn(
              "w-5 h-5 mx-auto mb-2",
              totalSkipped > 0 ? "text-amber-500" : "text-muted-foreground/30"
            )}
          />
          <p
            className={cn(
              "text-2xl font-bold",
              totalSkipped > 0 ? "text-amber-500" : "text-muted-foreground"
            )}
          >
            {totalSkipped.toLocaleString()}
          </p>
          <p className="text-xs text-muted-foreground">Total Events Skipped</p>
        </div>
        <div className="metric-card text-center">
          {anyMapperSaved ? (
            <CheckCircle className="w-5 h-5 text-emerald-500 mx-auto mb-2" />
          ) : (
            <XCircle className="w-5 h-5 text-muted-foreground/30 mx-auto mb-2" />
          )}
          <p className="text-2xl font-bold text-foreground">
            {anyMapperSaved ? "Yes" : "No"}
          </p>
          <p className="text-xs text-muted-foreground">Mapper Saved</p>
        </div>
      </div>

      {/* Per-file results */}
      <div className="metric-card">
        <h3 className="font-semibold text-foreground mb-3">
          Results by File
        </h3>
        <div className="space-y-2">
          {files.map((file) => {
            const result = results[file.id];
            if (!result) return null;

            const hasFileErrors = result.errors.length > 0;

            return (
              <div
                key={file.id}
                className={cn(
                  "p-3 rounded-lg border",
                  hasFileErrors
                    ? "border-amber-500/30 bg-amber-500/5"
                    : "border-emerald-500/30 bg-emerald-500/5"
                )}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileJson
                      className={cn(
                        "w-4 h-4",
                        hasFileErrors ? "text-amber-500" : "text-emerald-500"
                      )}
                    />
                    <span className="font-mono text-sm">{file.file.name}</span>
                    <span className="text-xs text-muted-foreground">
                      ({file.source})
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-sm">
                    <span className="text-emerald-500">
                      {result.events_ingested.toLocaleString()} ingested
                    </span>
                    {result.events_skipped > 0 && (
                      <span className="text-amber-500">
                        {result.events_skipped.toLocaleString()} skipped
                      </span>
                    )}
                  </div>
                </div>
                {result.run_id && (
                  <p className="text-xs text-muted-foreground mt-1">
                    Run ID: <span className="font-mono">{result.run_id}</span>
                  </p>
                )}
                {hasFileErrors && (
                  <div className="mt-2 text-xs text-amber-500">
                    {result.errors.slice(0, 3).map((err, i) => (
                      <div key={i}>
                        {err.line && `Line ${err.line}: `}
                        {err.error}
                      </div>
                    ))}
                    {result.errors.length > 3 && (
                      <div className="text-muted-foreground">
                        ...and {result.errors.length - 3} more errors
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Suggestions */}
      {Object.values(results).some((r) => r.suggestions.length > 0) && (
        <div className="metric-card">
          <h3 className="font-semibold text-foreground mb-3">Suggestions</h3>
          <ul className="space-y-2">
            {Array.from(
              new Set(Object.values(results).flatMap((r) => r.suggestions))
            ).map((suggestion, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <span className="text-cyan">Tip:</span>
                <span className="text-muted-foreground">{suggestion}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3">
        {onViewTimeline && (
          <button
            onClick={onViewTimeline}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-cyan hover:bg-cyan/90 text-background font-semibold rounded-lg transition-colors"
          >
            View in Timeline
            <ArrowRight className="w-4 h-4" />
          </button>
        )}
        {onIngestAnother && (
          <button
            onClick={onIngestAnother}
            className="px-4 py-3 bg-secondary hover:bg-secondary/80 text-foreground rounded-lg transition-colors"
          >
            Ingest More Files
          </button>
        )}
      </div>
    </div>
  );
}
