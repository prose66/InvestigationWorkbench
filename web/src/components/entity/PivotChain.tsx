"use client";

import { X, Filter, Zap } from "lucide-react";
import { usePivotStore } from "@/stores/pivotStore";
import { cn } from "@/lib/utils";

interface PivotChainProps {
  className?: string;
}

export function PivotChain({ className }: PivotChainProps) {
  const { pivotEntities, removePivotEntity, clearPivotEntities } =
    usePivotStore();

  if (pivotEntities.length === 0) {
    return null;
  }

  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-xl p-4 fade-in-up",
        "bg-gradient-to-r from-[hsl(173_40%_12%)] via-[hsl(220_18%_10%)] to-[hsl(220_18%_10%)]",
        "border border-[hsl(173_60%_30%/0.3)]",
        "glow-border",
        className
      )}
    >
      {/* Animated background effect */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute inset-0 bg-gradient-to-r from-cyan/10 via-transparent to-transparent animate-pulse" />
      </div>

      <div className="relative flex items-center gap-4">
        {/* Icon and label */}
        <div className="flex items-center gap-2 text-cyan">
          <div className="p-1.5 rounded-lg bg-cyan/10 pulse-glow">
            <Filter className="w-4 h-4" />
          </div>
          <span className="text-sm font-semibold tracking-wide uppercase">
            Active Filters
          </span>
          <Zap className="w-3 h-3 text-amber-400" />
        </div>

        {/* Filter chips */}
        <div className="flex flex-wrap gap-2 flex-1">
          {pivotEntities.map((entity, index) => (
            <span
              key={`${entity.type}-${entity.value}-${index}`}
              className={cn(
                "group inline-flex items-center gap-2 px-3 py-1.5 rounded-lg",
                "bg-gradient-to-r from-cyan/20 to-cyan/10",
                "border border-cyan/30",
                "text-sm font-medium",
                "transition-all duration-200",
                "hover:border-cyan/50 hover:from-cyan/25 hover:to-cyan/15",
                "fade-in-up",
                index === 0 && "delay-75",
                index === 1 && "delay-150",
                index === 2 && "delay-225"
              )}
              style={{ animationDelay: `${index * 50}ms` }}
            >
              <span className="text-cyan/70 text-xs uppercase tracking-wider">
                {entity.type}
              </span>
              <span className="text-foreground font-mono text-sm max-w-40 truncate">
                {entity.value}
              </span>
              <button
                onClick={() => removePivotEntity(index)}
                className={cn(
                  "ml-1 p-0.5 rounded-md",
                  "text-cyan/50 hover:text-cyan hover:bg-cyan/20",
                  "transition-all duration-150",
                  "opacity-60 group-hover:opacity-100"
                )}
                title={`Remove ${entity.type}=${entity.value}`}
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </span>
          ))}
        </div>

        {/* Clear all button */}
        <button
          onClick={clearPivotEntities}
          className={cn(
            "flex items-center gap-1.5 px-3 py-1.5 rounded-lg",
            "text-sm text-muted-foreground",
            "bg-secondary/50 border border-border",
            "hover:text-foreground hover:bg-secondary hover:border-cyan/30",
            "transition-all duration-200"
          )}
        >
          <X className="w-3.5 h-3.5" />
          Clear
        </button>
      </div>

      {/* Bottom accent line */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-cyan/50 to-transparent" />
    </div>
  );
}
