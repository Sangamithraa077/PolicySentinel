import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listRecommendations, getRecommendation, updateRecommendationStatus } from "@/services/recommendationService";
import type { ListRecommendationsParams } from "@/services/recommendationService";

export function useRecommendations(params: ListRecommendationsParams) {
  return useQuery({
    queryKey: [
      "recommendations",
      params.status,
      params.confidenceScore,
      params.limit,
      params.offset,
    ],
    queryFn: () => listRecommendations(params),
  });
}

export function useRecommendationDetails(recommendationId: string | undefined) {
  return useQuery({
    queryKey: ["recommendation", recommendationId],
    queryFn: () => getRecommendation(recommendationId!),
    enabled: Boolean(recommendationId),
  });
}

export function useUpdateRecommendationStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ recommendationId, status }: { recommendationId: string; status: string }) =>
      updateRecommendationStatus(recommendationId, status),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["recommendations"] });
      queryClient.invalidateQueries({ queryKey: ["recommendation", data.id] });
    },
  });
}
