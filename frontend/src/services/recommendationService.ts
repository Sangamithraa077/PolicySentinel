import { apiClient } from "@/services/apiClient";
import type { RecommendationListResponse, Recommendation } from "@/types/recommendation";

export interface ListRecommendationsParams {
  status?: string;
  confidenceScore?: number;
  limit?: number;
  offset?: number;
}

export async function listRecommendations(params: ListRecommendationsParams = {}): Promise<RecommendationListResponse> {
  const response = await apiClient.get<RecommendationListResponse>("/recommendations", {
    params: {
      status: params.status,
      confidence_score: params.confidenceScore,
      limit: params.limit ?? 50,
      offset: params.offset ?? 0,
    },
  });
  return response.data;
}

export async function getRecommendation(recommendationId: string): Promise<Recommendation> {
  const response = await apiClient.get<Recommendation>(`/recommendations/${recommendationId}`);
  return response.data;
}

export async function updateRecommendationStatus(
  recommendationId: string,
  status: string,
  reviewerName?: string,
  reviewComments?: string
): Promise<Recommendation> {
  const response = await apiClient.patch<Recommendation>(`/recommendations/${recommendationId}/status`, {
    status,
    reviewer_name: reviewerName,
    review_comments: reviewComments,
  });
  return response.data;
}
