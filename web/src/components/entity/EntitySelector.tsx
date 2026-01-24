"use client";

import { useState } from "react";
import { Search } from "lucide-react";
import { useEntities } from "@/hooks/useEntities";
import { usePivotContext } from "@/hooks/usePivotContext";
import { useCaseStore } from "@/stores/caseStore";
import { ENTITY_TYPES, type EntityType } from "@/lib/types";
import { cn } from "@/lib/utils";

interface EntitySelectorProps {
  caseId: string;
  className?: string;
  onEntitySelect?: (type: string, value: string) => void;
}

export function EntitySelector({
  caseId,
  className,
  onEntitySelect,
}: EntitySelectorProps) {
  const [entityType, setEntityType] = useState<EntityType>("host");
  const [searchValue, setSearchValue] = useState("");
  const { recentEntities } = useCaseStore();
  const { navigateToEntity, pivotToTimeline } = usePivotContext();

  const { data: entities, isLoading } = useEntities(caseId, entityType, 100);

  const filteredEntities = entities?.filter((e) =>
    e.entity_value.toLowerCase().includes(searchValue.toLowerCase())
  );

  const handleSelect = (value: string) => {
    if (onEntitySelect) {
      onEntitySelect(entityType, value);
    } else {
      navigateToEntity(entityType, value);
    }
    setSearchValue("");
  };

  return (
    <div className={cn("bg-card border rounded-lg p-4", className)}>
      <h3 className="font-semibold mb-3">Select Entity</h3>

      <div className="flex gap-3 mb-4">
        {/* Entity Type Selector */}
        <select
          value={entityType}
          onChange={(e) => setEntityType(e.target.value as EntityType)}
          className="px-3 py-2 border rounded-md bg-background text-sm"
        >
          {ENTITY_TYPES.map((type) => (
            <option key={type} value={type}>
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </option>
          ))}
        </select>

        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            placeholder={`Search ${entityType}s...`}
            className="w-full pl-10 pr-4 py-2 border rounded-md bg-background text-sm"
          />
        </div>
      </div>

      {/* Entity List */}
      <div className="max-h-48 overflow-y-auto border rounded-md">
        {isLoading ? (
          <div className="p-4 text-center text-muted-foreground text-sm">
            Loading...
          </div>
        ) : filteredEntities?.length === 0 ? (
          <div className="p-4 text-center text-muted-foreground text-sm">
            No entities found
          </div>
        ) : (
          <ul className="divide-y">
            {filteredEntities?.slice(0, 20).map((entity) => (
              <li
                key={entity.entity_value}
                className="flex items-center justify-between px-3 py-2 hover:bg-muted cursor-pointer text-sm"
                onClick={() => handleSelect(entity.entity_value)}
              >
                <span className="truncate">{entity.entity_value}</span>
                <span className="text-muted-foreground text-xs">
                  {entity.event_count} events
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Action Buttons */}
      {searchValue && (
        <div className="mt-3 flex gap-2">
          <button
            onClick={() => handleSelect(searchValue)}
            className="flex-1 px-3 py-2 bg-primary text-primary-foreground rounded-md text-sm hover:bg-primary/90"
          >
            View Entity
          </button>
          <button
            onClick={() => {
              pivotToTimeline(entityType, searchValue);
              setSearchValue("");
            }}
            className="px-3 py-2 border rounded-md text-sm hover:bg-muted"
          >
            Pivot to Timeline
          </button>
        </div>
      )}

      {/* Recent Entities */}
      {recentEntities.length > 0 && !searchValue && (
        <div className="mt-4">
          <p className="text-xs text-muted-foreground mb-2">Recent:</p>
          <div className="flex flex-wrap gap-2">
            {recentEntities.slice(0, 5).map((recent, idx) => (
              <button
                key={`${recent.type}-${recent.value}-${idx}`}
                onClick={() => navigateToEntity(recent.type, recent.value)}
                className="px-2 py-1 bg-muted rounded text-xs hover:bg-muted/80"
                title={`${recent.type}: ${recent.value}`}
              >
                {recent.value.slice(0, 15)}
                {recent.value.length > 15 ? "..." : ""}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
