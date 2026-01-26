"use client";

import { AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import { FieldMappingRow } from "./FieldMappingRow";
import {
  validateMappings,
  getUnifiedFields,
} from "@/lib/fieldSuggestions";
import { useIngestStore } from "@/stores/ingestStore";

interface FieldMappingTableProps {
  sourceFields: string[];
  mappings: Record<string, string | null>;
  onMappingChange: (sourceField: string, unifiedField: string | null) => void;
  sampleRow?: Record<string, unknown>;
  showFieldSources?: boolean;
}

export function FieldMappingTable({
  sourceFields,
  mappings,
  onMappingChange,
  sampleRow,
  showFieldSources = false,
}: FieldMappingTableProps) {
  const { files, fieldSources } = useIngestStore();
  const unifiedFields = getUnifiedFields();
  const { valid, missing } = validateMappings(mappings);

  // Build a map of fileId -> filename for display
  const fileNames: Record<string, string> = {};
  files.forEach((f) => {
    fileNames[f.id] = f.source || f.file.name;
  });

  return (
    <div className="space-y-4">
      {/* Validation warning */}
      {!valid && (
        <div
          className={cn(
            "flex items-start gap-3 p-4 rounded-lg",
            "bg-amber-500/10 border border-amber-500/30"
          )}
        >
          <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-amber-500">Missing required fields</p>
            <p className="text-sm text-muted-foreground mt-1">
              Please map the following required fields:{" "}
              {missing.map((f, i) => (
                <span key={f}>
                  <code className="text-amber-500 bg-amber-500/10 px-1 rounded">
                    {f}
                  </code>
                  {i < missing.length - 1 && ", "}
                </span>
              ))}
            </p>
          </div>
        </div>
      )}

      {/* Mapping table */}
      <div className="metric-card p-0 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border bg-secondary/30">
              <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Source Field
              </th>
              {showFieldSources && files.length > 1 && (
                <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  In Files
                </th>
              )}
              <th className="px-2 py-2 w-8" />
              <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Maps To
              </th>
            </tr>
          </thead>
          <tbody>
            {sourceFields.map((field) => {
              // Get which files have this field
              const fileIds = fieldSources[field] || [];
              const fileCount = fileIds.length;

              return (
                <tr
                  key={field}
                  className="border-b border-border/50 hover:bg-secondary/20"
                >
                  <td className="px-3 py-2">
                    <span className="font-mono text-foreground">{field}</span>
                    {sampleRow && sampleRow[field] !== undefined && (
                      <span className="block text-xs text-muted-foreground truncate max-w-[200px]">
                        e.g., {String(sampleRow[field]).substring(0, 50)}
                        {String(sampleRow[field]).length > 50 && "..."}
                      </span>
                    )}
                  </td>
                  {showFieldSources && files.length > 1 && (
                    <td className="px-3 py-2">
                      <div className="flex items-center gap-1">
                        {files.map((file) => {
                          const hasField = fileIds.includes(file.id);
                          return (
                            <span
                              key={file.id}
                              className={cn(
                                "w-2 h-2 rounded-full",
                                hasField ? "bg-cyan" : "bg-muted-foreground/20"
                              )}
                              title={
                                hasField
                                  ? `Present in ${fileNames[file.id]}`
                                  : `Not in ${fileNames[file.id]}`
                              }
                            />
                          );
                        })}
                        <span className="text-xs text-muted-foreground ml-1">
                          ({fileCount}/{files.length})
                        </span>
                      </div>
                    </td>
                  )}
                  <td className="px-2 py-2">
                    <span className="text-muted-foreground">&rarr;</span>
                  </td>
                  <td className="px-3 py-2">
                    <FieldMappingRow
                      sourceField={field}
                      unifiedField={mappings[field]}
                      unifiedFields={unifiedFields}
                      onChange={(unified) => onMappingChange(field, unified)}
                    />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-6 text-xs text-muted-foreground">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-emerald-500" />
          <span>Required field mapped</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-cyan/50" />
          <span>Optional field mapped</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-muted-foreground/30" />
          <span>Field ignored (goes to extras_json)</span>
        </div>
      </div>
    </div>
  );
}
