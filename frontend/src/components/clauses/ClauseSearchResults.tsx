import { HighlightedText } from "@/components/clauses/HighlightedText";
import type { Clause } from "@/types/clause";
import { clauseLabel } from "@/utils/clauseLabel";
import { getAncestors } from "@/utils/clauseTree";

interface ClauseSearchResultsProps {
  results: Clause[];
  keyword: string;
  selectedId: string | null;
  clausesById: Map<string, Clause>;
  onSelect: (id: string) => void;
}

/** Flat, order-preserving list of keyword matches — each result shows its
 * ancestor chain so the match still reads in its section context even
 * without the full tree around it. */
export function ClauseSearchResults({
  results,
  keyword,
  selectedId,
  clausesById,
  onSelect,
}: ClauseSearchResultsProps) {
  if (results.length === 0) {
    return (
      <p className="px-3 py-8 text-center text-sm text-neutral-500">
        No clauses match &ldquo;{keyword}&rdquo;.
      </p>
    );
  }

  return (
    <ul className="space-y-0.5">
      {results.map((clause) => {
        const ancestors = getAncestors(clause.id, clausesById);
        const isSelected = clause.id === selectedId;
        return (
          <li key={clause.id}>
            <button
              type="button"
              onClick={() => onSelect(clause.id)}
              className={`block w-full rounded-md px-3 py-2 text-left text-sm transition-colors ${
                isSelected
                  ? "bg-brand-50 dark:bg-brand-500/15"
                  : "hover:bg-surface-muted dark:hover:bg-neutral-800"
              }`}
            >
              {ancestors.length > 0 && (
                <p className="truncate text-xs text-neutral-400">
                  {ancestors.map((ancestor) => clauseLabel(ancestor)).join(" › ")}
                </p>
              )}
              <p
                className={`truncate font-medium ${
                  isSelected
                    ? "text-brand-700 dark:text-brand-100"
                    : "text-foreground dark:text-neutral-100"
                }`}
              >
                <HighlightedText text={clauseLabel(clause)} query={keyword} />
              </p>
            </button>
          </li>
        );
      })}
    </ul>
  );
}
