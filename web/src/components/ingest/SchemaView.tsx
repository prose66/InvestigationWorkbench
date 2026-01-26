"use client";

import { cn } from "@/lib/utils";
import { useIngestStore } from "@/stores/ingestStore";
import { CheckCircle } from "lucide-react";

export function SchemaView() {
  const { files, workingSchema, fieldSources, fieldMappings } = useIngestStore();

  // Get files that have previews
  const filesWithPreviews = files.filter((f) => f.previewData !== null);

  if (filesWithPreviews.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No files have been previewed yet.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="grid grid-cols-3 gap-4">
        <div className="metric-card text-center">
          <p className="text-2xl font-bold text-cyan">{filesWithPreviews.length}</p>
          <p className="text-xs text-muted-foreground">Files</p>
        </div>
        <div className="metric-card text-center">
          <p className="text-2xl font-bold text-cyan">{workingSchema.length}</p>
          <p className="text-xs text-muted-foreground">Unique Fields</p>
        </div>
        <div className="metric-card text-center">
          <p className="text-2xl font-bold text-cyan">
            {Object.values(fieldMappings).filter(Boolean).length}
          </p>
          <p className="text-xs text-muted-foreground">Auto-Mapped</p>
        </div>
      </div>

      {/* Field matrix */}
      <div className="metric-card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-secondary/30">
                <th className="px-3 py-2 text-left font-medium text-muted-foreground">
                  Source Field
                </th>
                {filesWithPreviews.map((file, idx) => (
                  <th
                    key={file.id}
                    className="px-3 py-2 text-center font-medium text-muted-foreground min-w-[80px]"
                    title={file.file.name}
                  >
                    <div className="truncate max-w-[100px]">
                      {file.source || `File ${idx + 1}`}
                    </div>
                    <div className="text-xs font-normal truncate max-w-[100px]">
                      {file.file.name}
                    </div>
                  </th>
                ))}
                <th className="px-3 py-2 text-left font-medium text-muted-foreground">
                  Suggested Mapping
                </th>
              </tr>
            </thead>
            <tbody>
              {workingSchema.map((field) => {
                const fileIds = fieldSources[field] || [];
                const suggestedMapping = fieldMappings[field];

                return (
                  <tr
                    key={field}
                    className="border-b border-border/50 hover:bg-secondary/20"
                  >
                    <td className="px-3 py-2 font-mono text-foreground">
                      {field}
                    </td>
                    {filesWithPreviews.map((file) => {
                      const hasField = fileIds.includes(file.id);
                      return (
                        <td key={file.id} className="px-3 py-2 text-center">
                          {hasField ? (
                            <span
                              className="inline-block w-3 h-3 rounded-full bg-cyan"
                              title={`Present in ${file.file.name}`}
                            />
                          ) : (
                            <span
                              className="inline-block w-3 h-3 rounded-full bg-muted-foreground/20"
                              title={`Not in ${file.file.name}`}
                            />
                          )}
                        </td>
                      );
                    })}
                    <td className="px-3 py-2">
                      {suggestedMapping ? (
                        <span
                          className={cn(
                            "inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs",
                            suggestedMapping === "event_ts" ||
                              suggestedMapping === "event_type"
                              ? "bg-emerald-500/10 text-emerald-500"
                              : "bg-cyan/10 text-cyan"
                          )}
                        >
                          {suggestedMapping}
                          {(suggestedMapping === "event_ts" ||
                            suggestedMapping === "event_type") && (
                            <CheckCircle className="w-3 h-3" />
                          )}
                        </span>
                      ) : (
                        <span className="text-muted-foreground text-xs">
                          (unmapped)
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-6 text-xs text-muted-foreground">
        <div className="flex items-center gap-2">
          <span className="inline-block w-3 h-3 rounded-full bg-cyan" />
          <span>Field present in file</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-block w-3 h-3 rounded-full bg-muted-foreground/20" />
          <span>Field not present (will be null)</span>
        </div>
      </div>

      {/* Note about missing fields */}
      <div className="p-3 rounded-lg bg-secondary/50 text-sm text-muted-foreground">
        <strong className="text-foreground">Note:</strong> Fields that are not
        present in a file will have <code className="text-cyan">null</code>{" "}
        values for events from that file. This allows you to combine data from
        different sources with different schemas.
      </div>
    </div>
  );
}
