"use client";

import { useQuery } from "@tanstack/react-query";
import { getEvents, getEvent, type EventFilterParams } from "@/lib/api";

export function useEvents(caseId: string | null, filters: EventFilterParams = {}) {
  return useQuery({
    queryKey: ["events", caseId, filters],
    queryFn: () => getEvents(caseId!, filters),
    enabled: !!caseId,
    staleTime: 30 * 1000, // 30 seconds
  });
}

export function useEvent(caseId: string | null, eventPk: number | null) {
  return useQuery({
    queryKey: ["event", caseId, eventPk],
    queryFn: () => getEvent(caseId!, eventPk!),
    enabled: !!caseId && !!eventPk,
    staleTime: 60 * 1000, // 1 minute
  });
}
