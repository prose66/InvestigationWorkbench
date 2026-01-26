"use client";

import {
  FileJson,
  ArrowRight,
  Users,
  Save,
  Clock,
  Files,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { validateMappings } from "@/lib/fieldSuggestions";
import { useIngestStore } from "@/stores/ingestStore";

interface IngestSummaryProps {
  saveMapper: boolean;
  onSaveMapperChange: (save: boolean) => void;
  timeStart?: string;
  timeEnd?: string;
  onTimeStartChange?: (time: string) => void;
  onTimeEndChange?: (time: string) => void;
}

export function IngestSummary({
  saveMapper,
  onSaveMapperChange,
  timeStart,
  timeEnd,
  onTimeStartChange,
  onTimeEndChange,
}: IngestSummaryProps) {
  const { files, fieldMappings, entityFields, getTotalRows } = useIngestStore();

  const { valid } = validateMappings(fieldMappings);
  const mappedCount = Object.values(fieldMappings).filter(Boolean).length;
  const ignoredCount = Object.values(fieldMappings).filter((v) => v === null).length;
  const totalRows = getTotalRows();

  // Get unique sources
  const uniqueSources = Array.from(new Set(files.map((f) => f.source)));

  return (
    <div className="space-y-6">
      {/* Files summary */}
      <div className="metric-card">
        <div className="flex items-center gap-2 mb-4">
          <Files className="w-4 h-4 text-cyan" />
          <h3 className="font-semibold text-foreground">
            Files ({files.length})
          </h3>
        </div>
        <div className="space-y-2">
          {files.map((file, idx) => (
            <div
              key={file.id}
              className="flex items-center justify-between p-2 rounded bg-secondary/30"
            >
              <div className="flex items-center gap-2">
                <FileJson className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm font-mono truncate max-w-[200px]">
                  {file.file.name}
                </span>
              </div>
              <div className="flex items-center gap-4 text-xs text-muted-foreground">
                <span>{file.source}</span>
                <span>
                  {file.previewData?.total_rows.toLocaleString() || 0} rows
                </span>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-3 pt-3 border-t border-border flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Total Rows</span>
          <span className="font-semibold text-foreground">
            {totalRows.toLocaleString()}
          </span>
        </div>
      </div>

      {/* Mapping summary */}
      <div className="metric-card">
        <div className="flex items-center gap-2 mb-4">
          <ArrowRight className="w-4 h-4 text-cyan" />
          <h3 className="font-semibold text-foreground">Field Mapping</h3>
        </div>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div className="p-3 rounded-lg bg-cyan/10">
            <p className="text-2xl font-bold text-cyan">{mappedCount}</p>
            <p className="text-xs text-muted-foreground">Fields Mapped</p>
          </div>
          <div className="p-3 rounded-lg bg-secondary/50">
            <p className="text-2xl font-bold text-muted-foreground">{ignoredCount}</p>
            <p className="text-xs text-muted-foreground">Fields Ignored</p>
          </div>
          <div
            className={cn(
              "p-3 rounded-lg",
              valid ? "bg-emerald-500/10" : "bg-amber-500/10"
            )}
          >
            <p
              className={cn(
                "text-2xl font-bold",
                valid ? "text-emerald-500" : "text-amber-500"
              )}
            >
              {valid ? "Ready" : "!"}
            </p>
            <p className="text-xs text-muted-foreground">Validation</p>
          </div>
        </div>
      </div>

      {/* Entity extraction */}
      <div className="metric-card">
        <div className="flex items-center gap-2 mb-4">
          <Users className="w-4 h-4 text-cyan" />
          <h3 className="font-semibold text-foreground">Entity Extraction</h3>
        </div>
        {entityFields.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {entityFields.map((field) => (
              <span
                key={field}
                className="px-2 py-1 rounded bg-cyan/10 text-cyan text-xs font-mono"
              >
                {field}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            No entity fields selected for extraction
          </p>
        )}
      </div>

      {/* Time range (optional) */}
      {onTimeStartChange && onTimeEndChange && (
        <div className="metric-card">
          <div className="flex items-center gap-2 mb-4">
            <Clock className="w-4 h-4 text-cyan" />
            <h3 className="font-semibold text-foreground">Time Range (Optional)</h3>
          </div>
          <p className="text-sm text-muted-foreground mb-3">
            Specify the time range covered by this query (for coverage analysis)
          </p>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-muted-foreground">Start Time (ISO8601)</label>
              <input
                type="datetime-local"
                value={timeStart || ""}
                onChange={(e) => onTimeStartChange(e.target.value)}
                className="w-full mt-1 px-3 py-2 bg-secondary/50 border border-border rounded-lg text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-cyan/50"
              />
            </div>
            <div>
              <label className="text-xs text-muted-foreground">End Time (ISO8601)</label>
              <input
                type="datetime-local"
                value={timeEnd || ""}
                onChange={(e) => onTimeEndChange(e.target.value)}
                className="w-full mt-1 px-3 py-2 bg-secondary/50 border border-border rounded-lg text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-cyan/50"
              />
            </div>
          </div>
        </div>
      )}

      {/* Save mapper option */}
      <div className="metric-card">
        <label className="flex items-start gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={saveMapper}
            onChange={(e) => onSaveMapperChange(e.target.checked)}
            className="mt-1 w-4 h-4 rounded border-border bg-secondary accent-cyan"
          />
          <div>
            <div className="flex items-center gap-2">
              <Save className="w-4 h-4 text-muted-foreground" />
              <span className="font-medium text-foreground">
                Save mapper for future imports
              </span>
            </div>
            <p className="text-sm text-muted-foreground mt-1">
              Create YAML configuration files so future imports from{" "}
              {uniqueSources.length === 1 ? (
                <span className="font-mono">{uniqueSources[0]}</span>
              ) : (
                <span>
                  {uniqueSources.map((s, i) => (
                    <span key={s}>
                      <span className="font-mono">{s}</span>
                      {i < uniqueSources.length - 1 && ", "}
                    </span>
                  ))}
                </span>
              )}{" "}
              use these mappings automatically.
            </p>
          </div>
        </label>
      </div>
    </div>
  );
}
