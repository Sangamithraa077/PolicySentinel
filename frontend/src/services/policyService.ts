import type { AxiosProgressEvent } from "axios";

import { apiClient } from "@/services/apiClient";
import type { PolicyDocumentUploadResponse, PolicyListResponse } from "@/types/policy";

export interface UploadPolicyDocumentParams {
  file: File;
  companyId: string;
  uploadedByUserId: string;
  policyTitle: string;
  versionNumber: number;
  description: string;
  signal?: AbortSignal;
  onProgress?: (percent: number) => void;
}

export async function uploadPolicyDocument(
  params: UploadPolicyDocumentParams,
): Promise<PolicyDocumentUploadResponse> {
  const formData = new FormData();
  formData.append("file", params.file);
  formData.append("company_id", params.companyId);
  formData.append("uploaded_by_user_id", params.uploadedByUserId);
  formData.append("policy_title", params.policyTitle);
  formData.append("version_number", String(params.versionNumber));
  if (params.description.trim()) {
    formData.append("description", params.description.trim());
  }

  const response = await apiClient.post<PolicyDocumentUploadResponse>(
    "/uploads/policies",
    formData,
    {
      signal: params.signal,
      onUploadProgress: (event: AxiosProgressEvent) => {
        if (!params.onProgress || !event.total) return;
        params.onProgress(Math.round((event.loaded / event.total) * 100));
      },
    },
  );
  return response.data;
}

export interface ListPoliciesParams {
  limit?: number;
  offset?: number;
}

export async function listPolicies(params: ListPoliciesParams = {}): Promise<PolicyListResponse> {
  const response = await apiClient.get<PolicyListResponse>("/policies", {
    params: {
      limit: params.limit ?? 20,
      offset: params.offset ?? 0,
    },
  });
  return response.data;
}

/** Direct download URL — a plain navigation/anchor click lets the browser
 * handle the Content-Disposition response itself; no need to route this
 * one through axios. */
export function policyDownloadUrl(policyId: string): string {
  return `${import.meta.env.VITE_API_BASE_URL}/policies/${policyId}/download`;
}
