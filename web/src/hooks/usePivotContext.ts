"use client";

import { useEffect, useCallback, useRef } from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import {
  usePivotStore,
  createPivotEntity,
  getPivotFilterParams,
  serializePivots,
  deserializePivots,
} from "@/stores/pivotStore";
import { useCaseStore } from "@/stores/caseStore";

export function usePivotContext() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const isHydratedRef = useRef(false);

  const {
    pivotEntities,
    addPivotEntity,
    removePivotEntity,
    clearPivotEntities,
    setPivotEntitySingle,
    setPivotEntities,
  } = usePivotStore();
  const { selectedCaseId, addRecentEntity } = useCaseStore();

  // Hydrate store from URL on first load
  useEffect(() => {
    if (isHydratedRef.current) return;
    const urlPivots = searchParams.get("pivots");
    if (urlPivots) {
      const entities = deserializePivots(urlPivots);
      if (entities.length > 0) {
        setPivotEntities(entities);
      }
    }
    isHydratedRef.current = true;
  }, [searchParams, setPivotEntities]);

  // Update URL when pivots change (but don't on initial hydration)
  const updateUrlWithPivots = useCallback(
    (entities: typeof pivotEntities, targetPath?: string) => {
      const newParams = new URLSearchParams(searchParams.toString());
      const serialized = serializePivots(entities);

      if (serialized) {
        newParams.set("pivots", serialized);
      } else {
        newParams.delete("pivots");
      }

      const queryString = newParams.toString();
      const basePath = targetPath || pathname;
      router.push(`${basePath}${queryString ? `?${queryString}` : ""}`, {
        scroll: false,
      });
    },
    [pathname, router, searchParams]
  );

  // Add entity to pivot chain and navigate to timeline
  const pivotToTimeline = useCallback(
    (type: string, value: string) => {
      const entity = createPivotEntity(type, value);
      const exists = pivotEntities.some(
        (e) => e.column === entity.column && e.value === entity.value
      );
      if (!exists) {
        const newEntities = [...pivotEntities, entity];
        addPivotEntity(entity);
        addRecentEntity(type, value);
        if (selectedCaseId) {
          updateUrlWithPivots(newEntities, `/cases/${selectedCaseId}/timeline`);
        }
      } else if (selectedCaseId) {
        router.push(`/cases/${selectedCaseId}/timeline`);
      }
    },
    [addPivotEntity, addRecentEntity, pivotEntities, router, selectedCaseId, updateUrlWithPivots]
  );

  // Replace pivot chain with single entity and navigate to timeline
  const pivotToTimelineSingle = useCallback(
    (type: string, value: string) => {
      const entity = createPivotEntity(type, value);
      setPivotEntitySingle(entity);
      addRecentEntity(type, value);
      if (selectedCaseId) {
        updateUrlWithPivots([entity], `/cases/${selectedCaseId}/timeline`);
      }
    },
    [addRecentEntity, selectedCaseId, setPivotEntitySingle, updateUrlWithPivots]
  );

  // Navigate to entity page
  const navigateToEntity = useCallback(
    (type: string, value: string) => {
      addRecentEntity(type, value);
      if (selectedCaseId) {
        router.push(
          `/cases/${selectedCaseId}/entity?type=${type}&value=${encodeURIComponent(value)}`
        );
      }
    },
    [addRecentEntity, router, selectedCaseId]
  );

  // Clear pivots and update URL
  const clearPivotsWithUrl = useCallback(() => {
    clearPivotEntities();
    updateUrlWithPivots([]);
  }, [clearPivotEntities, updateUrlWithPivots]);

  // Remove pivot and update URL
  const removePivotWithUrl = useCallback(
    (index: number) => {
      const newEntities = pivotEntities.filter((_, i) => i !== index);
      removePivotEntity(index);
      updateUrlWithPivots(newEntities);
    },
    [pivotEntities, removePivotEntity, updateUrlWithPivots]
  );

  // Get filter params for API calls
  const getFilterParams = () => getPivotFilterParams(pivotEntities);

  return {
    pivotEntities,
    addPivotEntity: (type: string, value: string) =>
      addPivotEntity(createPivotEntity(type, value)),
    removePivotEntity: removePivotWithUrl,
    clearPivotEntities: clearPivotsWithUrl,
    pivotToTimeline,
    pivotToTimelineSingle,
    navigateToEntity,
    getFilterParams,
    hasPivots: pivotEntities.length > 0,
  };
}
