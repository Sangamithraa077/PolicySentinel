import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listConflicts, getConflict, updateConflictStatus } from "@/services/conflictService";
import type { ListConflictsParams } from "@/services/conflictService";

export function useConflicts(params: ListConflictsParams) {
  return useQuery({
    queryKey: [
      "conflicts",
      params.policyId,
      params.severity,
      params.conflictType,
      params.status,
      params.search,
      params.limit,
      params.offset,
    ],
    queryFn: () => listConflicts(params),
  });
}

export function useConflictDetails(conflictId: string | undefined) {
  return useQuery({
    queryKey: ["conflict", conflictId],
    queryFn: () => getConflict(conflictId!),
    enabled: Boolean(conflictId),
  });
}

export function useUpdateConflictStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ conflictId, status }: { conflictId: string; status: string }) =>
      updateConflictStatus(conflictId, status),
    onSuccess: (data) => {
      // Invalidate both the list and the specific details
      queryClient.invalidateQueries({ queryKey: ["conflicts"] });
      queryClient.invalidateQueries({ queryKey: ["conflict", data.id] });
    },
  });
}
