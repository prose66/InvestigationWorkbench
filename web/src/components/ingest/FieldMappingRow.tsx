"use client";

import { CheckCircle, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  REQUIRED_FIELDS,
  getFieldDescription,
} from "@/lib/fieldSuggestions";

interface FieldMappingRowProps {
  sourceField: string;
  unifiedField: string | null;
  unifiedFields: string[];
  onChange: (unifiedField: string | null) => void;
  sampleValue?: unknown;
}

export function FieldMappingRow({
  sourceField,
  unifiedField,
  unifiedFields,
  onChange,
  sampleValue,
}: FieldMappingRowProps) {
  const isRequired = unifiedField && REQUIRED_FIELDS.includes(unifiedField);
  const isIgnored = unifiedField === null;

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-2">
        <select
          value={unifiedField || ""}
          onChange={(e) => onChange(e.target.value || null)}
          className={cn(
            "flex-1 bg-secondary/50 border border-border rounded-lg px-3 py-1.5 text-sm",
            "focus:outline-none focus:ring-2 focus:ring-cyan/50 focus:border-cyan",
            "transition-all duration-200",
            isIgnored && "text-muted-foreground",
            isRequired && "border-cyan/50"
          )}
        >
          <option value="">(ignore this field)</option>
          <optgroup label="Required">
            {REQUIRED_FIELDS.map((field) => (
              <option key={field} value={field}>
                {field}
              </option>
            ))}
          </optgroup>
          <optgroup label="Optional">
            {unifiedFields
              .filter((f) => !REQUIRED_FIELDS.includes(f))
              .map((field) => (
                <option key={field} value={field}>
                  {field}
                </option>
              ))}
          </optgroup>
        </select>

        {/* Status indicator */}
        {isRequired ? (
          <span title="Required field mapped">
            <CheckCircle className="w-4 h-4 text-emerald-500" />
          </span>
        ) : isIgnored ? (
          <span title="Field ignored">
            <XCircle className="w-4 h-4 text-muted-foreground/50" />
          </span>
        ) : (
          <span title="Field mapped">
            <CheckCircle className="w-4 h-4 text-cyan/50" />
          </span>
        )}
      </div>

      {/* Field description */}
      {unifiedField && (
        <p className="text-xs text-muted-foreground">
          {getFieldDescription(unifiedField)}
        </p>
      )}
    </div>
  );
}
