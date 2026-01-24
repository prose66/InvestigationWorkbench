"use client";

import { useQuery } from "@tanstack/react-query";
import {
  getEntities,
  getEntitySummary,
  getEntityRelationships,
} from "@/lib/api";
import type { EntityType } from "@/lib/types";

export function useEntities(
  caseId: string | null,
  entityType: EntityType,
  limit = 100
) {
  return useQuery({
    queryKey: ["entities", caseId, entityType, limit],
    queryFn: () => getEntities(caseId!, entityType, limit),
    enabled: !!caseId,
    staleTime: 60 * 1000, // 1 minute
  });
}

export function useEntitySummary(
  caseId: string | null,
  entityType: string | null,
  entityValue: string | null
) {
  return useQuery({
    queryKey: ["entity-summary", caseId, entityType, entityValue],
    queryFn: () => getEntitySummary(caseId!, entityType!, entityValue!),
    enabled: !!caseId && !!entityType && !!entityValue,
    staleTime: 60 * 1000,
  });
}

export function useEntityRelationships(
  caseId: string | null,
  entityType: string | null,
  entityValue: string | null,
  limit = 15
) {
  return useQuery({
    queryKey: ["entity-relationships", caseId, entityType, entityValue, limit],
    queryFn: () => getEntityRelationships(caseId!, entityType!, entityValue!, limit),
    enabled: !!caseId && !!entityType && !!entityValue,
    staleTime: 60 * 1000,
  });
}
