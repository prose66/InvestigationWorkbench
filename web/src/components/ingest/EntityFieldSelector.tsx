"use client";

import { Check, Users, Server, Network, Hash, Cpu } from "lucide-react";
import { cn } from "@/lib/utils";
import { ENTITY_FIELDS } from "@/lib/fieldSuggestions";

interface EntityFieldSelectorProps {
  sourceFields: string[];
  mappings: Record<string, string | null>;
  selectedFields: string[];
  onToggle: (field: string) => void;
}

const ENTITY_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  host: Server,
  user: Users,
  src_ip: Network,
  dest_ip: Network,
  file_hash: Hash,
  process_name: Cpu,
};

const ENTITY_DESCRIPTIONS: Record<string, string> = {
  host: "Hostnames and device names for pivoting",
  user: "Usernames and accounts for pivoting",
  src_ip: "Source IP addresses for network analysis",
  dest_ip: "Destination IP addresses for network analysis",
  file_hash: "File hashes for IOC correlation",
  process_name: "Process names for behavior analysis",
};

export function EntityFieldSelector({
  sourceFields,
  mappings,
  selectedFields,
  onToggle,
}: EntityFieldSelectorProps) {
  // Get fields that are mapped to entity types
  const entityCandidates = sourceFields.filter((field) => {
    const unified = mappings[field];
    return unified && ENTITY_FIELDS.includes(unified);
  });

  if (entityCandidates.length === 0) {
    return (
      <div className="metric-card text-center py-8">
        <p className="text-muted-foreground">
          No entity fields detected. Map fields to host, user, src_ip, dest_ip,
          file_hash, or process_name to enable entity extraction.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Select which fields should be extracted as entities for pivoting and
        relationship analysis.
      </p>

      <div className="grid gap-3 sm:grid-cols-2">
        {entityCandidates.map((sourceField) => {
          const unifiedField = mappings[sourceField]!;
          const isSelected = selectedFields.includes(sourceField);
          const Icon = ENTITY_ICONS[unifiedField] || Users;
          const description = ENTITY_DESCRIPTIONS[unifiedField];

          return (
            <button
              key={sourceField}
              onClick={() => onToggle(sourceField)}
              className={cn(
                "flex items-start gap-3 p-4 rounded-lg text-left transition-all duration-200",
                "border",
                isSelected
                  ? "bg-cyan/10 border-cyan/50"
                  : "bg-secondary/30 border-border hover:border-cyan/30"
              )}
            >
              {/* Checkbox */}
              <div
                className={cn(
                  "flex-shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center mt-0.5",
                  isSelected
                    ? "bg-cyan border-cyan"
                    : "border-border"
                )}
              >
                {isSelected && <Check className="w-3 h-3 text-background" />}
              </div>

              {/* Icon */}
              <div
                className={cn(
                  "p-2 rounded-lg flex-shrink-0",
                  isSelected ? "bg-cyan/20" : "bg-secondary"
                )}
              >
                <Icon
                  className={cn(
                    "w-4 h-4",
                    isSelected ? "text-cyan" : "text-muted-foreground"
                  )}
                />
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      "font-mono text-sm truncate",
                      isSelected ? "text-foreground" : "text-muted-foreground"
                    )}
                  >
                    {sourceField}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    ({unifiedField})
                  </span>
                </div>
                {description && (
                  <p className="text-xs text-muted-foreground mt-1">
                    {description}
                  </p>
                )}
              </div>
            </button>
          );
        })}
      </div>

      {/* Summary */}
      <div className="text-sm text-muted-foreground">
        {selectedFields.length === 0 ? (
          <span>No entity fields selected</span>
        ) : (
          <span>
            <span className="text-cyan font-medium">{selectedFields.length}</span>{" "}
            entity field{selectedFields.length !== 1 && "s"} selected for extraction
          </span>
        )}
      </div>
    </div>
  );
}
