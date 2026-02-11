"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getCases, getCaseSummary, createCase, deleteCase } from "@/lib/api";

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

export function useCreateCase() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ caseId, title }: { caseId: string; title?: string }) =>
      createCase(caseId, title),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cases"] });
    },
  });
}

export function useDeleteCase() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (caseId: string) => deleteCase(caseId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cases"] });
    },
  });
}
