import { useState, type FormEvent } from "react";
import {
  AlertCircle,
  Building2,
  Check,
  CheckCircle2,
  Moon,
  RotateCcw,
  Save,
  Sparkles,
  Sun,
  Trash2,
  XCircle,
} from "lucide-react";

import { ToastStack } from "@/components/common/Toast";
import { useCompanyDirectory } from "@/hooks/useCompanyDirectory";
import { useSystemMetadata } from "@/hooks/useSystemMetadata";
import { useTheme } from "@/hooks/useTheme";
import { useToasts } from "@/hooks/useToasts";
import { useWorkspace } from "@/hooks/useWorkspace";
import { API_BASE_URL } from "@/services/apiClient";
import { LANDING_PAGE_OPTIONS, ROWS_PER_PAGE_OPTIONS } from "@/utils/preferences";
import { isValidUuid } from "@/utils/validateUploadFile";

interface FieldErrors {
  companyId?: string;
  userId?: string;
}

export function SettingsPage() {
  const {
    identity,
    setIdentity,
    clearIdentity,
    preferences,
    setPreferences,
    resetPreferences,
    setCompanyNickname,
    companyLabel,
  } = useWorkspace();

  const [companyId, setCompanyId] = useState(identity.companyId);
  const [userId, setUserId] = useState(identity.userId);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [nicknameDrafts, setNicknameDrafts] = useState<Record<string, string>>({});

  const { theme, toggleTheme } = useTheme();
  const metadataQuery = useSystemMetadata();
  const directoryQuery = useCompanyDirectory();
  const { toasts, push: pushToast, dismiss: dismissToast } = useToasts();

  function handleSaveIdentity(event: FormEvent) {
    event.preventDefault();

    const errors: FieldErrors = {};
    if (companyId.trim() && !isValidUuid(companyId)) {
      errors.companyId = "Enter a valid UUID.";
    }
    if (userId.trim() && !isValidUuid(userId)) {
      errors.userId = "Enter a valid UUID.";
    }
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) return;

    setIdentity({ companyId: companyId.trim(), userId: userId.trim() });
    pushToast("success", "Workspace identity saved. Upload and dashboards will use this from now on.");
  }

  function handleClearIdentity() {
    clearIdentity();
    setCompanyId("");
    setUserId("");
    setFieldErrors({});
    pushToast("success", "Workspace identity cleared.");
  }

  function handleUseCompany(id: string) {
    setIdentity({ ...identity, companyId: id });
    setCompanyId(id);
    pushToast("success", `Now viewing ${companyLabel(id)}.`);
  }

  function handleSaveNickname(id: string) {
    const draft = (nicknameDrafts[id] ?? "").trim();
    if (!draft) return;
    setCompanyNickname(id, draft);
    pushToast("success", `Saved nickname "${draft}" for this company.`);
  }

  function handleSavePreferences(event: FormEvent) {
    event.preventDefault();
    pushToast("success", "Dashboard preferences saved.");
  }

  const directory = directoryQuery.data ?? [];

  return (
    <div className="flex flex-col gap-6">
      <ToastStack toasts={toasts} onDismiss={dismissToast} />

      <div>
        <h1 className="text-2xl font-semibold text-foreground dark:text-neutral-100">Settings</h1>
        <p className="mt-2 max-w-2xl text-sm text-neutral-500">
          Workspace identity, active company, dashboard behavior, and appearance for this browser.
        </p>
      </div>

      {/* Workspace Identity */}
      <section className="rounded-lg border border-border bg-surface p-6 shadow-sm dark:border-neutral-800 dark:bg-neutral-950">
        <h2 className="text-base font-semibold text-foreground dark:text-neutral-100">
          Workspace identity
        </h2>
        <p className="mt-1 max-w-2xl text-xs text-neutral-500">
          PolicySentinel doesn't have sign-in yet, so the Company ID and User ID on the Upload page
          are plain fields. Save them here once and they'll pre-fill automatically — and the Company
          ID also becomes the active company shown across every dashboard, filtered via the switcher
          in the top bar.
        </p>

        <form onSubmit={handleSaveIdentity} className="mt-5 flex flex-col gap-4 max-w-lg">
          <label className="block">
            <span className="mb-1.5 block text-sm font-medium text-foreground dark:text-neutral-100">
              Company ID
            </span>
            <div className="flex gap-2">
              <input
                type="text"
                value={companyId}
                onChange={(event) => setCompanyId(event.target.value)}
                placeholder="e.g. 6e671c26-dfd8-4ebe-832f-f5277432f865"
                className={inputClasses(Boolean(fieldErrors.companyId))}
              />
              <button
                type="button"
                onClick={() => setCompanyId(crypto.randomUUID())}
                title="Generate a new company ID"
                className="shrink-0 rounded-md border border-border px-3 text-neutral-500 hover:bg-neutral-50 hover:text-brand-600 dark:border-neutral-700 dark:hover:bg-neutral-800"
              >
                <Sparkles className="h-4 w-4" />
              </button>
            </div>
            {fieldErrors.companyId && <FieldError message={fieldErrors.companyId} />}
          </label>

          <label className="block">
            <span className="mb-1.5 block text-sm font-medium text-foreground dark:text-neutral-100">
              User ID
            </span>
            <div className="flex gap-2">
              <input
                type="text"
                value={userId}
                onChange={(event) => setUserId(event.target.value)}
                placeholder="e.g. f23c1df1-cb4f-4729-beb5-0b27315c9f2b"
                className={inputClasses(Boolean(fieldErrors.userId))}
              />
              <button
                type="button"
                onClick={() => setUserId(crypto.randomUUID())}
                title="Generate a new user ID"
                className="shrink-0 rounded-md border border-border px-3 text-neutral-500 hover:bg-neutral-50 hover:text-brand-600 dark:border-neutral-700 dark:hover:bg-neutral-800"
              >
                <Sparkles className="h-4 w-4" />
              </button>
            </div>
            {fieldErrors.userId && <FieldError message={fieldErrors.userId} />}
          </label>

          <div className="flex gap-2 pt-1">
            <button
              type="submit"
              className="flex items-center gap-1.5 rounded-md bg-brand-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-brand-700 transition-colors"
            >
              <Save className="h-3.5 w-3.5" />
              Save identity
            </button>
            <button
              type="button"
              onClick={handleClearIdentity}
              className="flex items-center gap-1.5 rounded-md border border-border px-3.5 py-2 text-xs font-semibold text-neutral-600 hover:bg-neutral-50 dark:border-neutral-800 dark:text-neutral-300 dark:hover:bg-neutral-800/80 transition-colors"
            >
              <Trash2 className="h-3.5 w-3.5" />
              Clear
            </button>
          </div>
        </form>
      </section>

      {/* Company directory */}
      <section className="rounded-lg border border-border bg-surface p-6 shadow-sm dark:border-neutral-800 dark:bg-neutral-950">
        <h2 className="text-base font-semibold text-foreground dark:text-neutral-100 flex items-center gap-2">
          <Building2 className="h-4 w-4 text-brand-500" />
          Company directory
        </h2>
        <p className="mt-1 max-w-2xl text-xs text-neutral-500">
          Discovered from the companies that currently have policies uploaded. Give each one a
          friendly nickname (there's no company-name lookup yet) and pick which one is active.
        </p>

        <div className="mt-5 flex flex-col gap-3">
          {directoryQuery.isLoading && (
            <p className="text-xs text-neutral-500">Loading companies…</p>
          )}

          {directory.length === 0 && !directoryQuery.isLoading && (
            <p className="text-xs text-neutral-500">
              No companies with policies yet — upload a policy first.
            </p>
          )}

          {directory.map((entry) => {
            const isActive = identity.companyId === entry.companyId;
            return (
              <div
                key={entry.companyId}
                className={`flex flex-col gap-3 rounded-md border p-3.5 sm:flex-row sm:items-center sm:justify-between ${
                  isActive
                    ? "border-brand-300 bg-brand-50/40 dark:border-brand-500/40 dark:bg-brand-500/5"
                    : "border-border dark:border-neutral-800"
                }`}
              >
                <div className="flex flex-col gap-1 min-w-0">
                  <span className="flex items-center gap-1.5 text-sm font-medium text-foreground dark:text-neutral-100">
                    {companyLabel(entry.companyId)}
                    {isActive && <Check className="h-3.5 w-3.5 text-brand-500" />}
                  </span>
                  <span className="font-mono text-[11px] text-neutral-400 truncate">
                    {entry.companyId}
                  </span>
                  <span className="text-xs text-neutral-500">
                    {entry.policyCount} {entry.policyCount === 1 ? "policy" : "policies"}
                  </span>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <input
                    type="text"
                    placeholder="Nickname"
                    defaultValue={preferences.companyNicknames[entry.companyId] ?? ""}
                    onChange={(event) =>
                      setNicknameDrafts((prev) => ({ ...prev, [entry.companyId]: event.target.value }))
                    }
                    className="w-36 rounded-md border border-border bg-surface px-2.5 py-1.5 text-xs text-foreground focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-100"
                  />
                  <button
                    type="button"
                    onClick={() => handleSaveNickname(entry.companyId)}
                    className="rounded-md border border-border px-2.5 py-1.5 text-xs font-semibold text-neutral-600 hover:bg-neutral-50 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800 transition-colors"
                  >
                    Save name
                  </button>
                  <button
                    type="button"
                    disabled={isActive}
                    onClick={() => handleUseCompany(entry.companyId)}
                    className="rounded-md bg-brand-600 px-2.5 py-1.5 text-xs font-semibold text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
                  >
                    {isActive ? "Active" : "Set active"}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Dashboard preferences */}
      <section className="rounded-lg border border-border bg-surface p-6 shadow-sm dark:border-neutral-800 dark:bg-neutral-950">
        <h2 className="text-base font-semibold text-foreground dark:text-neutral-100">
          Dashboard preferences
        </h2>
        <p className="mt-1 max-w-2xl text-xs text-neutral-500">
          Shapes how much data loads and where you land after opening the app.
        </p>

        <form onSubmit={handleSavePreferences} className="mt-5 flex flex-col gap-4 max-w-lg">
          <label className="block">
            <span className="mb-1.5 block text-sm font-medium text-foreground dark:text-neutral-100">
              Default landing page
            </span>
            <select
              value={preferences.landingPage}
              onChange={(event) =>
                setPreferences({
                  ...preferences,
                  landingPage: event.target.value as typeof preferences.landingPage,
                })
              }
              className={inputClasses(false)}
            >
              {LANDING_PAGE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="mb-1.5 block text-sm font-medium text-foreground dark:text-neutral-100">
              Rows per page
            </span>
            <select
              value={preferences.rowsPerPage}
              onChange={(event) =>
                setPreferences({ ...preferences, rowsPerPage: Number(event.target.value) })
              }
              className={inputClasses(false)}
            >
              {ROWS_PER_PAGE_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option} rows
                </option>
              ))}
            </select>
            <span className="mt-1.5 block text-xs text-neutral-400">
              Applies to policy, obligation, and audit-log lists.
            </span>
          </label>

          <div className="flex gap-2 pt-1">
            <button
              type="submit"
              className="flex items-center gap-1.5 rounded-md bg-brand-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-brand-700 transition-colors"
            >
              <Save className="h-3.5 w-3.5" />
              Save preferences
            </button>
            <button
              type="button"
              onClick={() => {
                resetPreferences();
                pushToast("success", "Dashboard preferences reset to defaults.");
              }}
              className="flex items-center gap-1.5 rounded-md border border-border px-3.5 py-2 text-xs font-semibold text-neutral-600 hover:bg-neutral-50 dark:border-neutral-800 dark:text-neutral-300 dark:hover:bg-neutral-800/80 transition-colors"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              Reset to defaults
            </button>
          </div>
        </form>
      </section>

      {/* Appearance */}
      <section className="rounded-lg border border-border bg-surface p-6 shadow-sm dark:border-neutral-800 dark:bg-neutral-950">
        <h2 className="text-base font-semibold text-foreground dark:text-neutral-100">Appearance</h2>
        <p className="mt-1 max-w-2xl text-xs text-neutral-500">
          Switch between light and dark themes. Saved automatically for this browser.
        </p>

        <button
          type="button"
          onClick={toggleTheme}
          className="mt-4 flex items-center gap-2 rounded-md border border-border px-3.5 py-2 text-xs font-semibold text-neutral-700 hover:bg-neutral-50 dark:border-neutral-800 dark:text-neutral-300 dark:hover:bg-neutral-800/80 transition-colors"
        >
          {theme === "light" ? <Moon className="h-3.5 w-3.5" /> : <Sun className="h-3.5 w-3.5" />}
          Switch to {theme === "light" ? "dark" : "light"} mode
        </button>
      </section>

      {/* System / Connection info */}
      <section className="rounded-lg border border-border bg-surface p-6 shadow-sm dark:border-neutral-800 dark:bg-neutral-950">
        <h2 className="text-base font-semibold text-foreground dark:text-neutral-100">
          System connection
        </h2>
        <p className="mt-1 max-w-2xl text-xs text-neutral-500">
          Confirms the frontend can reach the configured backend API.
        </p>

        <dl className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 max-w-lg text-sm">
          <div className="flex flex-col gap-0.5">
            <dt className="text-xs font-semibold uppercase tracking-wider text-neutral-400">
              API base URL
            </dt>
            <dd className="font-mono text-xs text-neutral-600 dark:text-neutral-300 break-all">
              {API_BASE_URL}
            </dd>
          </div>

          <div className="flex flex-col gap-0.5">
            <dt className="text-xs font-semibold uppercase tracking-wider text-neutral-400">
              Status
            </dt>
            <dd>
              {metadataQuery.isPending && (
                <span className="text-xs text-neutral-500">Checking…</span>
              )}
              {metadataQuery.isError && (
                <span className="flex items-center gap-1.5 text-xs font-medium text-red-600 dark:text-red-400">
                  <XCircle className="h-3.5 w-3.5" />
                  Unreachable
                </span>
              )}
              {metadataQuery.isSuccess && (
                <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-600 dark:text-emerald-400">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Connected
                </span>
              )}
            </dd>
          </div>

          {metadataQuery.data && (
            <>
              <div className="flex flex-col gap-0.5">
                <dt className="text-xs font-semibold uppercase tracking-wider text-neutral-400">
                  Service
                </dt>
                <dd className="text-xs text-neutral-600 dark:text-neutral-300">
                  {metadataQuery.data.name} v{metadataQuery.data.version}
                </dd>
              </div>
              <div className="flex flex-col gap-0.5">
                <dt className="text-xs font-semibold uppercase tracking-wider text-neutral-400">
                  API version
                </dt>
                <dd className="text-xs text-neutral-600 dark:text-neutral-300">
                  {metadataQuery.data.api_version}
                </dd>
              </div>
            </>
          )}
        </dl>
      </section>
    </div>
  );
}

function FieldError({ message }: { message: string }) {
  return (
    <p className="mt-1.5 flex items-center gap-1.5 text-xs text-red-600 dark:text-red-400">
      <AlertCircle className="h-3.5 w-3.5 shrink-0" />
      {message}
    </p>
  );
}

function inputClasses(hasError: boolean): string {
  const base =
    "w-full rounded-md border bg-surface px-3 py-2 text-sm text-foreground placeholder:text-neutral-400 focus:outline-none focus:ring-2 dark:bg-neutral-900 dark:text-neutral-100";
  return hasError
    ? `${base} border-red-400 focus:ring-red-400/40 dark:border-red-500/60`
    : `${base} border-border focus:border-brand-500 focus:ring-brand-500/30 dark:border-neutral-700`;
}

export default SettingsPage;
