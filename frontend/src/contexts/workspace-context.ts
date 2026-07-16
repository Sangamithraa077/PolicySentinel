import { createContext } from "react";

import type { Preferences } from "@/utils/preferences";
import type { WorkspaceIdentity } from "@/utils/workspaceIdentity";

export interface WorkspaceContextValue {
  identity: WorkspaceIdentity;
  setIdentity: (identity: WorkspaceIdentity) => void;
  clearIdentity: () => void;

  preferences: Preferences;
  setPreferences: (preferences: Preferences) => void;
  resetPreferences: () => void;

  setCompanyNickname: (companyId: string, nickname: string) => void;
  removeCompanyNickname: (companyId: string) => void;
  /** Display label for a company_id: its saved nickname, or a shortened
   * form of the UUID if none was set. */
  companyLabel: (companyId: string) => string;
}

export const WorkspaceContext = createContext<WorkspaceContextValue | undefined>(undefined);
