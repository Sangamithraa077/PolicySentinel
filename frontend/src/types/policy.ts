/**
 * Mirrors backend schemas/policies.py and schemas/uploads.py. Field names
 * match the API's JSON wire format (snake_case) directly rather than
 * introducing a camelCase translation layer.
 */

export type PolicyStatus = "draft" | "active" | "archived" | "superseded";

export type PolicyVersionStatus = "draft" | "under_review" | "published" | "superseded";

export type PolicyFileType = "txt" | "md" | "pdf" | "docx";

export interface PolicyVersionSummary {
  id: string;
  version_number: number;
  status: PolicyVersionStatus;
  original_filename: string;
  file_type: PolicyFileType;
  size_bytes: number;
  description: string | null;
  uploaded_by_user_id: string;
  uploaded_at: string;
  is_current: boolean;
}

export interface Policy {
  id: string;
  company_id: string;
  company_name?: string | null;
  title: string;
  policy_code: string | null;
  category: string | null;
  status: PolicyStatus;
  current_version: PolicyVersionSummary | null;
  created_at: string;
  updated_at: string;
}

export interface PolicyDetail extends Policy {
  owning_department_id: string | null;
  versions: PolicyVersionSummary[];
}

export interface PolicyListResponse {
  items: Policy[];
  total: number;
  limit: number;
  offset: number;
}

/** Response from POST /uploads/policies. */
export interface PolicyDocumentUploadResponse {
  original_filename: string;
  stored_filename: string;
  storage_path: string;
  extension: string;
  content_type: string;
  size_bytes: number;
  sha256: string;
  uploaded_at: string;
  policy_id: string;
  policy_version_id: string;
  company_id: string;
  policy_title: string;
  version_number: number;
  description: string | null;
  uploaded_by_user_id: string;
}
