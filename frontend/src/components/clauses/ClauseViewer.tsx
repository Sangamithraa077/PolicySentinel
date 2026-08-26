import { useMemo, useState } from "react";
import { FileWarning, Inbox, Loader2, RefreshCw, Search, X } from "lucide-react";

import { ClauseDetailPanel } from "@/components/clauses/ClauseDetailPanel";
import { ClauseSearchResults } from "@/components/clauses/ClauseSearchResults";
import { ClauseTreeRow } from "@/components/clauses/ClauseTreeRow";
import { useClauseSearch, useClauses } from "@/hooks/useClauses";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { resegmentClauses } from "@/services/clauseService";
import type { Clause } from "@/types/clause";
import { extractApiErrorMessage } from "@/utils/apiError";
import { buildClauseTree, collectParentIds } from "@/utils/clauseTree";

const MAX_SHOWN_NOTICE_THRESHOLD = 200;

export function ClauseViewer({ policyId }: { policyId: string }) {
  const [keyword, setKeyword] = useState("");
  const [collapsedIds, setCollapsedIds] = useState<Set<string>>(new Set());
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [isResegmenting, setIsResegmenting] = useState(false);

  const debouncedKeyword = useDebouncedValue(keyword, 300);
  const isSearching = debouncedKeyword.trim().length > 0;

  const clausesQuery = useClauses(policyId);
  const searchQuery = useClauseSearch(policyId, debouncedKeyword);

  async function handleResegment() {
    const versionId = clausesQuery.data?.items[0]?.policy_version_id;
    if (!versionId) return;
    setIsResegmenting(true);
    try {
      await resegmentClauses(versionId, true);
      await clausesQuery.refetch();
    } catch (err) {
      console.error("Failed to re-segment clauses:", err);
    } finally {
      setIsResegmenting(false);
    }
  }

  const clauses = useMemo(() => clausesQuery.data?.items ?? [], [clausesQuery.data]);
  const clausesById = useMemo(
    () => new Map(clauses.map((clause): [string, Clause] => [clause.id, clause])),
    [clauses],
  );
  const tree = useMemo(() => buildClauseTree(clauses), [clauses]);
  const parentIds = useMemo(() => collectParentIds(clauses), [clauses]);

  const searchResults = searchQuery.data?.items ?? [];
  const selectedClause =
    clausesById.get(selectedId ?? "") ??
    searchResults.find((clause) => clause.id === selectedId) ??
    null;

  function toggleCollapsed(id: string) {
    setCollapsedIds((current) => {
      const next = new Set(current);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
      <div className="flex flex-col rounded-lg border border-border bg-surface lg:col-span-2 dark:border-neutral-800 dark:bg-neutral-900">
        <div className="space-y-3 border-b border-border p-4 dark:border-neutral-800">
          <div className="relative">
            <Search className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-neutral-400" />
            <input
              type="text"
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
              placeholder="Search clauses…"
              className="w-full rounded-md border border-border bg-surface py-2 pr-9 pl-9 text-sm text-foreground placeholder:text-neutral-400 focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30 focus:outline-none dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-100"
            />
            {keyword && (
              <button
                type="button"
                onClick={() => setKeyword("")}
                aria-label="Clear search"
                className="absolute top-1/2 right-2.5 -translate-y-1/2 rounded p-0.5 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>

          {!isSearching && (
            <div className="flex items-center justify-between text-xs text-neutral-500">
              {parentIds.size > 0 ? (
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => setCollapsedIds(new Set())}
                    className="font-medium text-brand-600 hover:underline dark:text-brand-400"
                  >
                    Expand all
                  </button>
                  <button
                    type="button"
                    onClick={() => setCollapsedIds(new Set(parentIds))}
                    className="font-medium text-brand-600 hover:underline dark:text-brand-400"
                  >
                    Collapse all
                  </button>
                </div>
              ) : (
                <span />
              )}
              {clauses.length > 0 && clauses[0]?.policy_version_id && (
                <button
                  type="button"
                  disabled={isResegmenting}
                  onClick={handleResegment}
                  className="flex items-center gap-1.5 rounded bg-brand-50 px-2 py-1 font-medium text-brand-700 hover:bg-brand-100 disabled:opacity-50 dark:bg-brand-950/40 dark:text-brand-300 dark:hover:bg-brand-900/60"
                  title="Re-run clause segmentation with AI structure fallback"
                >
                  <RefreshCw className={`h-3 w-3 ${isResegmenting ? "animate-spin" : ""}`} />
                  {isResegmenting ? "Resegmenting…" : "Re-segment"}
                </button>
              )}
            </div>
          )}
        </div>

        <div className="max-h-[65vh] flex-1 overflow-y-auto p-3">
          {clausesQuery.isPending && (
            <div className="flex items-center gap-2 px-2 py-8 text-sm text-neutral-500">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading clauses…
            </div>
          )}

          {clausesQuery.isError && (
            <div className="flex items-start gap-2 px-2 py-8 text-sm text-red-600 dark:text-red-400">
              <FileWarning className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{extractApiErrorMessage(clausesQuery.error, "Couldn't load clauses.")}</span>
            </div>
          )}

          {clausesQuery.isSuccess && clauses.length === 0 && (
            <div className="flex flex-col items-center gap-2 px-2 py-10 text-center text-sm text-neutral-500">
              <Inbox className="h-8 w-8 text-neutral-300 dark:text-neutral-700" />
              This policy has no clauses yet.
            </div>
          )}

          {clausesQuery.isSuccess && clauses.length > 0 && isSearching && (
            <>
              {searchQuery.isPending && (
                <div className="flex items-center gap-2 px-2 py-8 text-sm text-neutral-500">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Searching…
                </div>
              )}
              {searchQuery.isError && (
                <div className="flex items-start gap-2 px-2 py-8 text-sm text-red-600 dark:text-red-400">
                  <FileWarning className="mt-0.5 h-4 w-4 shrink-0" />
                  <span>{extractApiErrorMessage(searchQuery.error, "Search failed.")}</span>
                </div>
              )}
              {searchQuery.isSuccess && (
                <ClauseSearchResults
                  results={searchResults}
                  keyword={debouncedKeyword}
                  selectedId={selectedId}
                  clausesById={clausesById}
                  onSelect={setSelectedId}
                />
              )}
            </>
          )}

          {clausesQuery.isSuccess && clauses.length > 0 && !isSearching && (
            <>
              {clausesQuery.data.total > MAX_SHOWN_NOTICE_THRESHOLD && (
                <p className="mb-2 px-2 text-xs text-amber-600 dark:text-amber-400">
                  Showing the first {clauses.length} of {clausesQuery.data.total} clauses.
                </p>
              )}
              <ul>
                {tree.map((node) => (
                  <ClauseTreeRow
                    key={node.id}
                    node={node}
                    depth={0}
                    selectedId={selectedId}
                    collapsedIds={collapsedIds}
                    onSelect={setSelectedId}
                    onToggle={toggleCollapsed}
                  />
                ))}
              </ul>
            </>
          )}
        </div>
      </div>

      <div className="min-h-[24rem] rounded-lg border border-border bg-surface lg:col-span-3 dark:border-neutral-800 dark:bg-neutral-900">
        <ClauseDetailPanel clause={selectedClause} clausesById={clausesById} />
      </div>
    </div>
  );
}
