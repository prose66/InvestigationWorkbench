"use client";

import { useRouter } from "next/navigation";
import {
  usePivotStore,
  createPivotEntity,
  getPivotFilterParams,
} from "@/stores/pivotStore";
import { useCaseStore } from "@/stores/caseStore";

export function usePivotContext() {
  const router = useRouter();
  const {
    pivotEntities,
    addPivotEntity,
    removePivotEntity,
    clearPivotEntities,
    setPivotEntitySingle,
  } = usePivotStore();
  const { selectedCaseId, addRecentEntity } = useCaseStore();

  // Add entity to pivot chain and navigate to timeline
  const pivotToTimeline = (type: string, value: string) => {
    addPivotEntity(createPivotEntity(type, value));
    addRecentEntity(type, value);
    if (selectedCaseId) {
      router.push(`/cases/${selectedCaseId}/timeline`);
    }
  };

  // Replace pivot chain with single entity and navigate to timeline
  const pivotToTimelineSingle = (type: string, value: string) => {
    setPivotEntitySingle(createPivotEntity(type, value));
    addRecentEntity(type, value);
    if (selectedCaseId) {
      router.push(`/cases/${selectedCaseId}/timeline`);
    }
  };

  // Navigate to entity page
  const navigateToEntity = (type: string, value: string) => {
    addRecentEntity(type, value);
    if (selectedCaseId) {
      router.push(
        `/cases/${selectedCaseId}/entity?type=${type}&value=${encodeURIComponent(value)}`
      );
    }
  };

  // Get filter params for API calls
  const getFilterParams = () => getPivotFilterParams(pivotEntities);

  return {
    pivotEntities,
    addPivotEntity: (type: string, value: string) =>
      addPivotEntity(createPivotEntity(type, value)),
    removePivotEntity,
    clearPivotEntities,
    pivotToTimeline,
    pivotToTimelineSingle,
    navigateToEntity,
    getFilterParams,
    hasPivots: pivotEntities.length > 0,
  };
}
