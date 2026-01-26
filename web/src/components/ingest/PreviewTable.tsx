"use client";

import { cn } from "@/lib/utils";

interface PreviewTableProps {
  fields: string[];
  rows: Record<string, unknown>[];
  maxRows?: number;
  highlightFields?: string[];
}

export function PreviewTable({
  fields,
  rows,
  maxRows = 10,
  highlightFields = [],
}: PreviewTableProps) {
  const displayRows = rows.slice(0, maxRows);

  return (
    <div className="metric-card p-0 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-secondary/30">
              {fields.map((field) => (
                <th
                  key={field}
                  className={cn(
                    "px-3 py-2 text-left font-medium whitespace-nowrap",
                    highlightFields.includes(field)
                      ? "text-cyan"
                      : "text-muted-foreground"
                  )}
                >
                  {field}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayRows.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                className="border-b border-border/50 hover:bg-secondary/20"
              >
                {fields.map((field) => {
                  const value = row[field];
                  const displayValue = formatCellValue(value);
                  return (
                    <td
                      key={field}
                      className="px-3 py-2 max-w-[200px] truncate text-foreground"
                      title={displayValue}
                    >
                      {displayValue || (
                        <span className="text-muted-foreground/50">-</span>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {rows.length > maxRows && (
        <div className="px-3 py-2 text-xs text-muted-foreground border-t border-border bg-secondary/20">
          Showing {maxRows} of {rows.length} rows
        </div>
      )}
    </div>
  );
}

function formatCellValue(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
