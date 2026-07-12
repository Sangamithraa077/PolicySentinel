import { useState } from "react";
import { Loader2, Search, FileText } from "lucide-react";
import type { Obligation } from "@/types/obligation";
import { useObligations } from "@/hooks/useObligations";
import { useClauseDetails } from "@/hooks/useClauses";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { extractApiErrorMessage } from "@/utils/apiError";

interface ObligationViewerProps {
  policyId: string;
}

export function ObligationViewer({ policyId }: ObligationViewerProps) {
  const [keywordInput, setKeywordInput] = useState("");
  const debouncedKeyword = useDebouncedValue(keywordInput, 300);
  const [selectedModality, setSelectedModality] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [selectedObligation, setSelectedObligation] = useState<Obligation | null>(null);

  // 1. Fetch obligations with active filters
  const obligationsQuery = useObligations({
    policyId,
    keyword: debouncedKeyword,
    modality: selectedModality || undefined,
    complianceCategory: selectedCategory || undefined,
  });

  // 2. Fetch original clause for the selected obligation
  const clauseQuery = useClauseDetails(selectedObligation?.clause_id);

  // 3. Extract unique categories from items
  const allObligationsQueryForCategories = useObligations({ policyId });
  const uniqueCategories = Array.from(
    new Set(
      (allObligationsQueryForCategories.data?.items ?? []).map((o) => o.compliance_category)
    )
  ).filter(Boolean);

  const handleRowClick = (ob: Obligation) => {
    setSelectedObligation(ob);
  };

  const getModalityBadgeClass = (modality: string) => {
    const mod = modality.toLowerCase();
    if (mod === "must" || mod === "shall") {
      return "bg-red-50 text-red-700 ring-red-600/10 dark:bg-red-500/10 dark:text-red-400 dark:ring-red-500/20";
    }
    if (mod === "should") {
      return "bg-blue-50 text-blue-700 ring-blue-600/10 dark:bg-blue-500/10 dark:text-blue-400 dark:ring-blue-500/20";
    }
    return "bg-green-50 text-green-700 ring-green-600/10 dark:bg-green-500/10 dark:text-green-400 dark:ring-green-500/20";
  };

  const getConfidenceColorClass = (score: number) => {
    if (score >= 0.9) return "text-green-600 dark:text-green-400 font-semibold";
    if (score >= 0.7) return "text-amber-600 dark:text-amber-400";
    return "text-red-600 dark:text-red-400";
  };

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      {/* Search & Filters + Obligations List Table */}
      <div className="lg:col-span-2 flex flex-col gap-4">
        {/* Controls */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          {/* Keyword Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-neutral-400" />
            <input
              type="text"
              placeholder="Search obligations..."
              value={keywordInput}
              onChange={(e) => setKeywordInput(e.target.value)}
              className="w-full rounded-md border border-border bg-surface pl-9 pr-3 py-2 text-sm text-foreground focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-100"
            />
          </div>

          {/* Modality Filter */}
          <select
            value={selectedModality}
            onChange={(e) => setSelectedModality(e.target.value)}
            className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-100 sm:w-44"
          >
            <option value="">All Modalities</option>
            <option value="Must">Must</option>
            <option value="Shall">Shall</option>
            <option value="Should">Should</option>
            <option value="May">May</option>
          </select>

          {/* Compliance Category Filter */}
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-100 sm:w-48"
          >
            <option value="">All Categories</option>
            {uniqueCategories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>

        {/* Table/List */}
        <div className="rounded-lg border border-border bg-surface overflow-hidden dark:border-neutral-800 dark:bg-neutral-900">
          {obligationsQuery.isPending && (
            <div className="flex flex-col items-center justify-center p-12 gap-2 text-sm text-neutral-500">
              <Loader2 className="h-6 w-6 animate-spin text-brand-600" />
              Loading obligations...
            </div>
          )}

          {obligationsQuery.isError && (
            <div className="p-8 text-center text-sm text-red-600 dark:text-red-400">
              {extractApiErrorMessage(obligationsQuery.error, "Failed to load obligations.")}
            </div>
          )}

          {obligationsQuery.isSuccess && (
            <>
              {obligationsQuery.data.items.length === 0 ? (
                <div className="p-12 text-center text-sm text-neutral-500">
                  No compliance obligations found matching your criteria.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="border-b border-border bg-surface-muted/50 text-xs font-semibold text-neutral-500 dark:border-neutral-800 dark:bg-neutral-950/50 dark:text-neutral-400">
                        <th className="px-4 py-3">Subject</th>
                        <th className="px-4 py-3">Action</th>
                        <th className="px-4 py-3">Modality</th>
                        <th className="px-4 py-3">Category</th>
                        <th className="px-4 py-3 text-right">Confidence</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border dark:divide-neutral-800 text-sm">
                      {obligationsQuery.data.items.map((ob) => (
                        <tr
                          key={ob.id}
                          onClick={() => handleRowClick(ob)}
                          className={`cursor-pointer hover:bg-surface-muted/65 transition-colors ${
                            selectedObligation?.id === ob.id
                              ? "bg-brand-50/50 hover:bg-brand-50/60 dark:bg-brand-500/5 dark:hover:bg-brand-500/10"
                              : ""
                          }`}
                        >
                          <td className="px-4 py-3.5 font-medium text-foreground dark:text-neutral-200">
                            {ob.subject}
                          </td>
                          <td className="px-4 py-3.5 text-neutral-600 dark:text-neutral-400">
                            {ob.action} <span className="text-neutral-400 dark:text-neutral-500">{ob.object}</span>
                          </td>
                          <td className="px-4 py-3.5">
                            <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${getModalityBadgeClass(ob.modality)}`}>
                              {ob.modality}
                            </span>
                          </td>
                          <td className="px-4 py-3.5 text-xs text-neutral-500 dark:text-neutral-400">
                            {ob.compliance_category}
                          </td>
                          <td className="px-4 py-3.5 text-right font-mono text-xs">
                            <span className={getConfidenceColorClass(ob.confidence_score)}>
                              {Math.round(ob.confidence_score * 100)}%
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Detail Panel */}
      <div className="lg:col-span-1 border border-border bg-surface rounded-lg p-5 dark:border-neutral-800 dark:bg-neutral-900 flex flex-col gap-5">
        {!selectedObligation ? (
          <div className="flex h-64 flex-col items-center justify-center gap-2 text-center text-sm text-neutral-500">
            <FileText className="h-8 w-8 text-neutral-300 dark:text-neutral-700" />
            Select an obligation from the list to view its analysis and source clause.
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            <div>
              <h3 className="text-lg font-semibold text-foreground dark:text-neutral-100">
                Obligation details
              </h3>
              <p className="text-xs text-neutral-400 mt-0.5">
                AI extraction using model <span className="font-mono text-neutral-500 dark:text-neutral-300">{selectedObligation.ai_model}</span>
              </p>
            </div>

            {/* Structured attributes */}
            <div className="space-y-3">
              <div>
                <span className="text-xs font-semibold text-neutral-400 block uppercase tracking-wider">Subject (who)</span>
                <span className="text-sm font-medium text-foreground dark:text-neutral-200">{selectedObligation.subject}</span>
              </div>
              <div>
                <span className="text-xs font-semibold text-neutral-400 block uppercase tracking-wider">Action (what)</span>
                <span className="text-sm text-neutral-700 dark:text-neutral-300">
                  <span className="font-medium italic text-foreground dark:text-neutral-200">{selectedObligation.action}</span> {selectedObligation.object}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-xs font-semibold text-neutral-400 block uppercase tracking-wider">Modality</span>
                  <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${getModalityBadgeClass(selectedObligation.modality)}`}>
                    {selectedObligation.modality}
                  </span>
                </div>
                <div>
                  <span className="text-xs font-semibold text-neutral-400 block uppercase tracking-wider">Category</span>
                  <span className="text-sm text-neutral-700 dark:text-neutral-300">{selectedObligation.compliance_category}</span>
                </div>
              </div>

              {selectedObligation.conditions && (
                <div>
                  <span className="text-xs font-semibold text-neutral-400 block uppercase tracking-wider">Conditions</span>
                  <span className="text-sm text-neutral-700 dark:text-neutral-300">{selectedObligation.conditions}</span>
                </div>
              )}

              {selectedObligation.time_constraint && (
                <div>
                  <span className="text-xs font-semibold text-neutral-400 block uppercase tracking-wider">Time constraints</span>
                  <span className="text-sm text-neutral-700 dark:text-neutral-300">{selectedObligation.time_constraint}</span>
                </div>
              )}
            </div>

            <hr className="border-border dark:border-neutral-800" />

            {/* Original clause */}
            <div>
              <h4 className="text-sm font-semibold text-foreground dark:text-neutral-100 mb-2">
                Original policy clause
              </h4>
              <div className="rounded-md border border-border bg-surface-muted/50 p-3.5 dark:border-neutral-800 dark:bg-neutral-950/50">
                {clauseQuery.isPending && (
                  <div className="flex items-center gap-2 text-xs text-neutral-500">
                    <Loader2 className="h-3 w-3 animate-spin" />
                    Fetching source clause...
                  </div>
                )}
                {clauseQuery.isError && (
                  <span className="text-xs text-red-500">Could not retrieve original clause.</span>
                )}
                {clauseQuery.isSuccess && (
                  <div>
                    {clauseQuery.data.clause_number && (
                      <span className="inline-block rounded bg-neutral-200/60 dark:bg-neutral-800 px-1.5 py-0.5 text-xs font-semibold text-neutral-600 dark:text-neutral-400 mb-1.5">
                        Clause {clauseQuery.data.clause_number}
                      </span>
                    )}
                    {clauseQuery.data.heading && (
                      <h5 className="text-xs font-semibold text-neutral-700 dark:text-neutral-300 mb-1">
                        {clauseQuery.data.heading}
                      </h5>
                    )}
                    <p className="text-xs leading-relaxed text-neutral-600 dark:text-neutral-400 italic whitespace-pre-wrap">
                      "{clauseQuery.data.text}"
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
