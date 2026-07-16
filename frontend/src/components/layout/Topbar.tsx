import { useRef, useState } from "react";
import { Building2, Check, ChevronDown, Moon, Settings, Sun } from "lucide-react";
import { Link } from "react-router-dom";

import { useCompanyDirectory } from "@/hooks/useCompanyDirectory";
import { useTheme } from "@/hooks/useTheme";
import { useWorkspace } from "@/hooks/useWorkspace";
import { useClickOutside } from "@/hooks/useClickOutside";

export function Topbar() {
  const { theme, toggleTheme } = useTheme();
  const { identity, setIdentity, companyLabel } = useWorkspace();
  const directoryQuery = useCompanyDirectory();
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  useClickOutside(menuRef, () => setOpen(false));

  const directory = directoryQuery.data ?? [];
  const hasActiveCompany = Boolean(identity.companyId);

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-border bg-surface/80 px-6 backdrop-blur-md dark:border-neutral-800 dark:bg-neutral-900/80">
      <div className="relative" ref={menuRef}>
        <button
          type="button"
          onClick={() => setOpen((prev) => !prev)}
          className="flex items-center gap-2 rounded-full border border-border bg-surface-muted/60 px-3.5 py-1.5 text-sm font-medium text-neutral-700 hover:bg-surface-muted dark:border-neutral-700 dark:bg-neutral-800/60 dark:text-neutral-200 dark:hover:bg-neutral-800 transition-colors"
        >
          <Building2 className="h-4 w-4 text-brand-500" />
          {hasActiveCompany ? companyLabel(identity.companyId) : "All companies"}
          <ChevronDown className="h-3.5 w-3.5 text-neutral-400" />
        </button>

        {open && (
          <div className="absolute left-0 top-full z-20 mt-2 w-72 rounded-xl border border-border bg-surface py-1.5 shadow-xl shadow-black/5 dark:border-neutral-700 dark:bg-neutral-900">
            <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-neutral-400">
              Switch workspace
            </div>

            {directoryQuery.isLoading && (
              <div className="px-3 py-2 text-xs text-neutral-500">Loading companies…</div>
            )}

            {directory.length === 0 && !directoryQuery.isLoading && (
              <div className="px-3 py-2 text-xs text-neutral-500">
                No companies with policies yet.
              </div>
            )}

            {directory.map((entry) => (
              <button
                key={entry.companyId}
                type="button"
                onClick={() => {
                  setIdentity({ ...identity, companyId: entry.companyId });
                  setOpen(false);
                }}
                className="flex w-full items-center justify-between gap-2 px-3 py-2 text-left text-xs hover:bg-surface-muted dark:hover:bg-neutral-800 transition-colors"
              >
                <span className="flex flex-col">
                  <span className="font-medium text-foreground dark:text-neutral-100">
                    {companyLabel(entry.companyId)}
                  </span>
                  <span className="text-neutral-400">
                    {entry.policyCount} {entry.policyCount === 1 ? "policy" : "policies"}
                  </span>
                </span>
                {identity.companyId === entry.companyId && (
                  <Check className="h-3.5 w-3.5 shrink-0 text-brand-500" />
                )}
              </button>
            ))}

            <div className="mt-1 border-t border-border pt-1 dark:border-neutral-800">
              <Link
                to="/settings"
                onClick={() => setOpen(false)}
                className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-neutral-500 hover:bg-surface-muted hover:text-foreground dark:hover:bg-neutral-800 dark:hover:text-neutral-100 transition-colors"
              >
                <Settings className="h-3.5 w-3.5" />
                Manage in Settings
              </Link>
            </div>
          </div>
        )}
      </div>

      <button
        type="button"
        onClick={toggleTheme}
        aria-label="Toggle color theme"
        className="rounded-full border border-border bg-surface-muted/60 p-2 text-neutral-500 transition-colors hover:bg-surface-muted hover:text-foreground dark:border-neutral-700 dark:bg-neutral-800/60 dark:text-neutral-400 dark:hover:bg-neutral-800 dark:hover:text-neutral-100"
      >
        {theme === "light" ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
      </button>
    </header>
  );
}
