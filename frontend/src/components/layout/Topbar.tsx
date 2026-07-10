import { Moon, Sun } from "lucide-react";

import { useTheme } from "@/hooks/useTheme";

export function Topbar() {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="flex h-16 shrink-0 items-center justify-end border-b border-border bg-surface px-6 dark:border-neutral-800 dark:bg-neutral-900">
      <button
        type="button"
        onClick={toggleTheme}
        aria-label="Toggle color theme"
        className="rounded-md p-2 text-neutral-500 transition-colors hover:bg-surface-muted hover:text-foreground dark:text-neutral-400 dark:hover:bg-neutral-800 dark:hover:text-neutral-100"
      >
        {theme === "light" ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
      </button>
    </header>
  );
}
