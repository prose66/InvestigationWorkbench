"use client";

import { X } from "lucide-react";
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
        "flex items-center gap-2 p-3 bg-blue-50 border border-blue-200 rounded-lg",
        className
      )}
    >
      <span className="text-sm font-medium text-blue-800">Filters:</span>
      <div className="flex flex-wrap gap-2">
        {pivotEntities.map((entity, index) => (
          <span
            key={`${entity.type}-${entity.value}-${index}`}
            className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
          >
            <span className="font-medium">{entity.type}:</span>
            <span className="max-w-32 truncate">{entity.value}</span>
            <button
              onClick={() => removePivotEntity(index)}
              className="ml-1 hover:bg-blue-200 rounded-full p-0.5"
              title={`Remove ${entity.type}=${entity.value}`}
            >
              <X className="w-3 h-3" />
            </button>
          </span>
        ))}
      </div>
      <button
        onClick={clearPivotEntities}
        className="ml-auto text-sm text-blue-600 hover:text-blue-800 hover:underline"
      >
        Clear All
      </button>
    </div>
  );
}
