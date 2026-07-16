import { useCallback, useMemo, useState, type ReactNode } from "react";

import { WorkspaceContext, type WorkspaceContextValue } from "@/contexts/workspace-context";
import {
  DEFAULT_PREFERENCES,
  clearStoredPreferences,
  getStoredPreferences,
  setStoredPreferences,
  type Preferences,
} from "@/utils/preferences";
import {
  clearStoredWorkspaceIdentity,
  getStoredWorkspaceIdentity,
  setStoredWorkspaceIdentity,
  type WorkspaceIdentity,
} from "@/utils/workspaceIdentity";

const EMPTY_IDENTITY: WorkspaceIdentity = { companyId: "", userId: "" };

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [identity, setIdentityState] = useState<WorkspaceIdentity>(getStoredWorkspaceIdentity);
  const [preferences, setPreferencesState] = useState<Preferences>(getStoredPreferences);

  const setIdentity = useCallback((next: WorkspaceIdentity) => {
    setStoredWorkspaceIdentity(next);
    setIdentityState(next);
  }, []);

  const clearIdentity = useCallback(() => {
    clearStoredWorkspaceIdentity();
    setIdentityState(EMPTY_IDENTITY);
  }, []);

  const setPreferences = useCallback((next: Preferences) => {
    setStoredPreferences(next);
    setPreferencesState(next);
  }, []);

  const resetPreferences = useCallback(() => {
    clearStoredPreferences();
    setPreferencesState(DEFAULT_PREFERENCES);
  }, []);

  const setCompanyNickname = useCallback(
    (companyId: string, nickname: string) => {
      const next: Preferences = {
        ...preferences,
        companyNicknames: { ...preferences.companyNicknames, [companyId]: nickname },
      };
      setStoredPreferences(next);
      setPreferencesState(next);
    },
    [preferences],
  );

  const removeCompanyNickname = useCallback(
    (companyId: string) => {
      const nicknames = { ...preferences.companyNicknames };
      delete nicknames[companyId];
      const next: Preferences = { ...preferences, companyNicknames: nicknames };
      setStoredPreferences(next);
      setPreferencesState(next);
    },
    [preferences],
  );

  const companyLabel = useCallback(
    (companyId: string) => {
      const nickname = preferences.companyNicknames[companyId];
      if (nickname) return nickname;
      return companyId ? `Company ${companyId.slice(0, 8)}` : "Unknown company";
    },
    [preferences.companyNicknames],
  );

  const value = useMemo<WorkspaceContextValue>(
    () => ({
      identity,
      setIdentity,
      clearIdentity,
      preferences,
      setPreferences,
      resetPreferences,
      setCompanyNickname,
      removeCompanyNickname,
      companyLabel,
    }),
    [
      identity,
      setIdentity,
      clearIdentity,
      preferences,
      setPreferences,
      resetPreferences,
      setCompanyNickname,
      removeCompanyNickname,
      companyLabel,
    ],
  );

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}
