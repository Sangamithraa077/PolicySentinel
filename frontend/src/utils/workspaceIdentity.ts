/**
 * Until real sign-in exists, every screen that needs a company/user
 * identity (Upload, Reports, ...) asks for plain UUIDs (see
 * UploadPage.tsx). This persists the last-used pair in localStorage so
 * the identity only has to be entered once per browser, from Settings.
 */

import { isValidUuid } from "@/utils/validateUploadFile";

const STORAGE_KEY = "policysentinel-workspace-identity";

export interface WorkspaceIdentity {
  companyId: string;
  userId: string;
}

const EMPTY_IDENTITY: WorkspaceIdentity = { companyId: "", userId: "" };

export function getStoredWorkspaceIdentity(): WorkspaceIdentity {
  if (typeof window === "undefined") return EMPTY_IDENTITY;

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return EMPTY_IDENTITY;

    const parsed = JSON.parse(raw) as Partial<WorkspaceIdentity>;
    const companyId = typeof parsed.companyId === "string" ? parsed.companyId : "";
    const userId = typeof parsed.userId === "string" ? parsed.userId : "";
    return { companyId, userId };
  } catch {
    return EMPTY_IDENTITY;
  }
}

export function setStoredWorkspaceIdentity(identity: WorkspaceIdentity): void {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(identity));
}

export function clearStoredWorkspaceIdentity(): void {
  window.localStorage.removeItem(STORAGE_KEY);
}

export function isCompleteWorkspaceIdentity(identity: WorkspaceIdentity): boolean {
  return isValidUuid(identity.companyId) && isValidUuid(identity.userId);
}
