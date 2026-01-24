"use client";

import { useQuery } from "@tanstack/react-query";
import { getCases, getCaseSummary } from "@/lib/api";

export function useCases() {
  return useQuery({
    queryKey: ["cases"],
    queryFn: getCases,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useCaseSummary(caseId: string | null) {
  return useQuery({
    queryKey: ["case-summary", caseId],
    queryFn: () => getCaseSummary(caseId!),
    enabled: !!caseId,
    staleTime: 60 * 1000, // 1 minute
  });
}
