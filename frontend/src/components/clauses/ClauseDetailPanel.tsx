import { ScrollText } from "lucide-react";

import type { Clause } from "@/types/clause";
import { getAncestors } from "@/utils/clauseTree";

interface ClauseDetailPanelProps {
  clause: Clause | null;
  clausesById: Map<string, Clause>;
}

/** Full text of the selected clause, with its section-hierarchy
 * breadcrumb above it — the detail view for "Highlight selected
 * clause" (selection is highlighted in the list; this is what it's
 * highlighting *to*). */
export function ClauseDetailPanel({ clause, clausesById }: ClauseDetailPanelProps) {
  if (!clause) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2 p-8 text-center text-sm text-neutral-500">
        <ScrollText className="h-8 w-8 text-neutral-300 dark:text-neutral-700" />
        Select a clause to view its full text.
      </div>
    );
  }

  const ancestors = getAncestors(clause.id, clausesById);

  return (
    <div className="flex h-full flex-col overflow-y-auto p-5">
      {ancestors.length > 0 && (
        <nav
          aria-label="Section hierarchy"
          className="mb-3 flex flex-wrap items-center gap-1 text-xs text-neutral-400"
        >
          {ancestors.map((ancestor) => (
            <span key={ancestor.id} className="flex items-center gap-1">
              <span>{ancestor.clause_number ?? ancestor.heading ?? "…"}</span>
              <span aria-hidden="true">›</span>
            </span>
          ))}
        </nav>
      )}

      <div className="mb-4 flex flex-wrap items-baseline gap-2">
        {clause.clause_number && (
          <span className="shrink-0 rounded bg-surface-muted px-2 py-0.5 text-xs font-semibold text-neutral-500 dark:bg-neutral-800 dark:text-neutral-400">
            {clause.clause_number}
          </span>
        )}
        {clause.heading && (
          <h2 className="text-base font-semibold text-foreground dark:text-neutral-100">
            {clause.heading}
          </h2>
        )}
      </div>

      <p className="whitespace-pre-wrap text-sm leading-relaxed text-neutral-700 dark:text-neutral-300">
        {clause.text}
      </p>
    </div>
  );
}
