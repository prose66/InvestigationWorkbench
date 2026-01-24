"use client";

import { useState } from "react";
import { Search, ChevronDown, Sparkles, History, ArrowRight } from "lucide-react";
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
  const [isFocused, setIsFocused] = useState(false);
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
    <div
      className={cn(
        "relative overflow-hidden rounded-xl p-5",
        "card-gradient border border-border",
        isFocused && "glow-border",
        "transition-all duration-300",
        className
      )}
    >
      {/* Top accent line */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-cyan/50 to-transparent" />

      <div className="flex items-center gap-2 mb-4">
        <div className="p-1.5 rounded-lg bg-cyan/10">
          <Sparkles className="w-4 h-4 text-cyan" />
        </div>
        <h3 className="font-semibold text-foreground">Entity Explorer</h3>
      </div>

      <div className="flex gap-3 mb-4">
        {/* Entity Type Selector */}
        <div className="relative">
          <select
            value={entityType}
            onChange={(e) => setEntityType(e.target.value as EntityType)}
            className={cn(
              "appearance-none px-4 py-2.5 pr-10 rounded-lg text-sm font-medium",
              "bg-secondary border border-border",
              "text-foreground cursor-pointer",
              "hover:border-cyan/30 focus:outline-none focus:border-cyan/50 focus:ring-2 focus:ring-cyan/20",
              "transition-all duration-200"
            )}
          >
            {ENTITY_TYPES.map((type) => (
              <option key={type} value={type}>
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </option>
            ))}
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
        </div>

        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder={`Search ${entityType}s...`}
            className="input-dark pl-10"
          />
        </div>
      </div>

      {/* Entity List */}
      <div
        className={cn(
          "max-h-48 overflow-y-auto rounded-lg",
          "bg-background/50 border border-border/50"
        )}
      >
        {isLoading ? (
          <div className="p-4 text-center">
            <div className="inline-block animate-spin rounded-full h-5 w-5 border-2 border-cyan border-t-transparent" />
          </div>
        ) : filteredEntities?.length === 0 ? (
          <div className="p-4 text-center text-muted-foreground text-sm">
            No entities found
          </div>
        ) : (
          <ul className="divide-y divide-border/30">
            {filteredEntities?.slice(0, 20).map((entity, index) => (
              <li
                key={entity.entity_value}
                className={cn(
                  "flex items-center justify-between px-4 py-2.5",
                  "hover:bg-cyan/5 cursor-pointer",
                  "transition-colors duration-150",
                  "fade-in-up"
                )}
                style={{ animationDelay: `${index * 20}ms` }}
                onClick={() => handleSelect(entity.entity_value)}
              >
                <span className="font-mono text-sm truncate text-foreground">
                  {entity.entity_value}
                </span>
                <span className="text-xs text-cyan/70 font-medium">
                  {entity.event_count.toLocaleString()} events
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Action Buttons */}
      {searchValue && (
        <div className="mt-4 flex gap-2 fade-in-up">
          <button
            onClick={() => handleSelect(searchValue)}
            className="btn-primary flex-1 flex items-center justify-center gap-2"
          >
            View Entity
            <ArrowRight className="w-4 h-4" />
          </button>
          <button
            onClick={() => {
              pivotToTimeline(entityType, searchValue);
              setSearchValue("");
            }}
            className="btn-ghost border border-border"
          >
            Add to Filters
          </button>
        </div>
      )}

      {/* Recent Entities */}
      {recentEntities.length > 0 && !searchValue && (
        <div className="mt-4 pt-4 border-t border-border/30">
          <div className="flex items-center gap-2 mb-2">
            <History className="w-3 h-3 text-muted-foreground" />
            <p className="text-xs text-muted-foreground uppercase tracking-wider font-medium">
              Recent
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {recentEntities.slice(0, 5).map((recent, idx) => (
              <button
                key={`${recent.type}-${recent.value}-${idx}`}
                onClick={() => navigateToEntity(recent.type, recent.value)}
                className={cn(
                  "px-2.5 py-1 rounded-md text-xs font-mono",
                  "bg-secondary/50 border border-border/50",
                  "text-muted-foreground hover:text-foreground hover:border-cyan/30",
                  "transition-all duration-200",
                  "fade-in-up"
                )}
                style={{ animationDelay: `${idx * 50}ms` }}
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
