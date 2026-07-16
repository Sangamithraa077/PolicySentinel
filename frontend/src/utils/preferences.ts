/**
 * Local, per-browser dashboard preferences — separate from
 * workspaceIdentity.ts (which holds the company/user UUIDs used for
 * uploads and as the active-tenant filter). Nothing here is sent to the
 * backend; it only shapes how the frontend presents data.
 */

const STORAGE_KEY = "policysentinel-preferences";

export const LANDING_PAGE_OPTIONS = [
  { value: "/", label: "Dashboard" },
  { value: "/policies", label: "Policies" },
  { value: "/conflicts", label: "Conflicts" },
  { value: "/recommendations", label: "Recommendations" },
  { value: "/regulatory-dashboard", label: "Regulatory Dashboard" },
  { value: "/reports", label: "Reports" },
] as const;

export type LandingPage = (typeof LANDING_PAGE_OPTIONS)[number]["value"];

export const ROWS_PER_PAGE_OPTIONS = [10, 20, 50, 100] as const;

export interface Preferences {
  landingPage: LandingPage;
  rowsPerPage: number;
  /** company_id -> a friendly display name the user assigned it, since the
   * API has no endpoint that returns a company's name. */
  companyNicknames: Record<string, string>;
}

export const DEFAULT_PREFERENCES: Preferences = {
  landingPage: "/",
  rowsPerPage: 20,
  companyNicknames: {},
};

export function getStoredPreferences(): Preferences {
  if (typeof window === "undefined") return DEFAULT_PREFERENCES;

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_PREFERENCES;

    const parsed = JSON.parse(raw) as Partial<Preferences>;
    return {
      landingPage: isLandingPage(parsed.landingPage) ? parsed.landingPage : DEFAULT_PREFERENCES.landingPage,
      rowsPerPage:
        typeof parsed.rowsPerPage === "number" && parsed.rowsPerPage > 0
          ? parsed.rowsPerPage
          : DEFAULT_PREFERENCES.rowsPerPage,
      companyNicknames:
        parsed.companyNicknames && typeof parsed.companyNicknames === "object"
          ? parsed.companyNicknames
          : {},
    };
  } catch {
    return DEFAULT_PREFERENCES;
  }
}

export function setStoredPreferences(preferences: Preferences): void {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
}

export function clearStoredPreferences(): void {
  window.localStorage.removeItem(STORAGE_KEY);
}

function isLandingPage(value: unknown): value is LandingPage {
  return typeof value === "string" && LANDING_PAGE_OPTIONS.some((opt) => opt.value === value);
}
