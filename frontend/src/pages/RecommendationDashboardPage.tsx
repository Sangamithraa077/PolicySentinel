import { useState } from "react";
import { Loader2, CheckCircle2, XCircle, ShieldAlert, Sparkles, Filter, ChevronRight } from "lucide-react";

import { useRecommendations, useUpdateRecommendationStatus } from "@/hooks/useRecommendations";
import type { Recommendation } from "@/types/recommendation";

export function RecommendationDashboardPage() {
  const [selectedStatus, setSelectedStatus] = useState("");
  const [minConfidence, setMinConfidence] = useState<number | "">("");
  const [selectedRecommendation, setSelectedRecommendation] = useState<Recommendation | null>(null);

  // Fetch recommendations
  const { data, isLoading, isError, refetch } = useRecommendations({
    status: selectedStatus || undefined,
    confidenceScore: minConfidence !== "" ? Number(minConfidence) : undefined,
  });

  // Mutator for Accept/Reject
  const updateStatusMutation = useUpdateRecommendationStatus();

  const handleStatusUpdate = async (recommendationId: string, status: string) => {
    try {
      const updated = await updateStatusMutation.mutateAsync({ recommendationId, status });
      setSelectedRecommendation(updated);
    } catch (err) {
      console.error("Failed to update status", err);
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status.toLowerCase()) {
      case "accepted":
        return "bg-green-50 text-green-700 ring-green-600/10 dark:bg-green-500/10 dark:text-green-400 dark:ring-green-500/20";
      case "rejected":
        return "bg-red-50 text-red-700 ring-red-600/10 dark:bg-red-500/10 dark:text-red-400 dark:ring-red-500/20";
      default:
        return "bg-amber-50 text-amber-700 ring-amber-600/10 dark:bg-amber-500/10 dark:text-amber-400 dark:ring-amber-500/20";
    }
  };

  return (
    <div className="flex flex-col h-full gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground dark:text-neutral-100 flex items-center gap-2">
          <Sparkles className="h-6 w-6 text-brand-500" />
          AI Resolution Recommendations
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-neutral-500">
          Review smart resolutions, suggested action maps, and legal clause redlines compiled by Gemini to resolve policy compliance gaps.
        </p>
      </div>

      {/* Filter and Content Split Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3 items-start">
        
        {/* Left Columns - Filters and Table */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            {/* Status Filter */}
            <div className="relative flex-1">
              <select
                value={selectedStatus}
                onChange={(e) => {
                  setSelectedStatus(e.target.value);
                  setSelectedRecommendation(null);
                }}
                className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-100"
              >
                <option value="">All Statuses</option>
                <option value="Pending">Pending</option>
                <option value="Accepted">Accepted</option>
                <option value="Rejected">Rejected</option>
              </select>
            </div>

            {/* Confidence score filter */}
            <div className="relative flex-1">
              <input
                type="number"
                step="0.05"
                min="0"
                max="1"
                placeholder="Min Confidence (e.g. 0.85)"
                value={minConfidence}
                onChange={(e) => {
                  const val = e.target.value;
                  setMinConfidence(val === "" ? "" : Number(val));
                  setSelectedRecommendation(null);
                }}
                className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-100"
              />
            </div>
          </div>

          {/* List Card */}
          <div className="overflow-hidden rounded-lg border border-border bg-surface shadow-sm dark:border-neutral-800 dark:bg-neutral-950">
            {isLoading ? (
              <div className="flex items-center justify-center p-12">
                <Loader2 className="h-8 w-8 animate-spin text-brand-500" />
              </div>
            ) : isError ? (
              <div className="flex flex-col items-center justify-center p-12 text-center">
                <ShieldAlert className="h-10 w-10 text-red-500" />
                <p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">Failed to load recommendations</p>
                <button onClick={() => refetch()} className="mt-4 text-xs font-semibold text-brand-600 hover:text-brand-500">
                  Try Again
                </button>
              </div>
            ) : data?.items.length === 0 ? (
              <div className="p-12 text-center text-sm text-neutral-500 dark:text-neutral-400">
                No resolution recommendations found matching current criteria.
              </div>
            ) : (
              <div className="divide-y divide-border dark:divide-neutral-800">
                {data?.items.map((rec) => (
                  <button
                    key={rec.id}
                    onClick={() => setSelectedRecommendation(rec)}
                    className={`w-full flex items-start justify-between p-4 text-left hover:bg-neutral-50 dark:hover:bg-neutral-900/50 transition-colors ${
                      selectedRecommendation?.id === rec.id ? "bg-brand-50/50 dark:bg-brand-500/5" : ""
                    }`}
                  >
                    <div className="flex flex-col gap-1.5 max-w-[80%]">
                      <span className="text-sm font-medium text-foreground dark:text-neutral-100">
                        {rec.recommendation_summary}
                      </span>
                      <div className="flex flex-wrap items-center gap-2 text-xs text-neutral-500">
                        <span className="font-semibold px-2 py-0.5 rounded bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300">
                          {rec.suggested_action}
                        </span>
                        <span>•</span>
                        <span>Confidence: {(rec.confidence_score * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset ${getStatusBadgeClass(rec.status)}`}>
                        {rec.status}
                      </span>
                      <ChevronRight className="h-4 w-4 text-neutral-400" />
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column - Detail Pane */}
        <div className="lg:col-span-1">
          {selectedRecommendation ? (
            <div className="rounded-lg border border-border bg-surface p-5 shadow-sm dark:border-neutral-800 dark:bg-neutral-950 flex flex-col gap-6">
              <div>
                <h2 className="text-base font-semibold text-foreground dark:text-neutral-100">
                  Resolution Details
                </h2>
                <div className="mt-2 inline-flex items-center rounded bg-neutral-50 border border-border px-2.5 py-1 text-xs font-mono dark:bg-neutral-900 dark:border-neutral-800 text-neutral-600 dark:text-neutral-300">
                  Model: {selectedRecommendation.ai_model}
                </div>
              </div>

              {/* Action Recommendation */}
              <div className="flex flex-col gap-1">
                <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider">
                  Summary & Resolution Suggestion
                </span>
                <p className="text-sm text-foreground dark:text-neutral-200">
                  {selectedRecommendation.recommendation_summary}
                </p>
              </div>

              {/* Suggested Action */}
              <div className="flex flex-col gap-1">
                <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider">
                  Suggested Action Path
                </span>
                <p className="text-sm text-foreground dark:text-neutral-200 font-medium">
                  {selectedRecommendation.suggested_action}
                </p>
              </div>

              {/* Reason for change */}
              <div className="flex flex-col gap-1">
                <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider">
                  Reason for change
                </span>
                <p className="text-sm text-neutral-600 dark:text-neutral-300 italic">
                  {selectedRecommendation.reason}
                </p>
              </div>

              {/* Redline comparative Box */}
              <div className="flex flex-col gap-3">
                <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider">
                  Suggested Redline Revision
                </span>
                <div className="flex flex-col gap-3 rounded-md bg-neutral-50 dark:bg-neutral-900 border border-border p-3">
                  <div className="flex flex-col gap-1">
                    <span className="text-xs font-semibold text-red-500">Original Clause</span>
                    <p className="text-xs font-mono text-neutral-600 dark:text-neutral-400 max-h-32 overflow-y-auto whitespace-pre-wrap">
                      {selectedRecommendation.original_clause || "No original clause."}
                    </p>
                  </div>
                  <div className="border-t border-dashed border-border my-1" />
                  <div className="flex flex-col gap-1">
                    <span className="text-xs font-semibold text-green-500">Revised Clause Suggestion</span>
                    <p className="text-xs font-mono text-neutral-900 dark:text-neutral-200 max-h-32 overflow-y-auto whitespace-pre-wrap bg-green-500/5 p-1 rounded">
                      {selectedRecommendation.revised_clause || "No revised clause suggestion."}
                    </p>
                  </div>
                </div>
              </div>

              {/* Actions Box */}
              {selectedRecommendation.status === "Pending" && (
                <div className="flex items-center gap-3 border-t border-border pt-4">
                  <button
                    onClick={() => handleStatusUpdate(selectedRecommendation.id, "Accepted")}
                    disabled={updateStatusMutation.isPending}
                    className="flex-1 flex items-center justify-center gap-1.5 rounded-md bg-green-600 hover:bg-green-500 active:bg-green-700 disabled:opacity-50 text-white py-2 text-sm font-semibold transition-colors"
                  >
                    <CheckCircle2 className="h-4 w-4" />
                    Accept
                  </button>
                  <button
                    onClick={() => handleStatusUpdate(selectedRecommendation.id, "Rejected")}
                    disabled={updateStatusMutation.isPending}
                    className="flex-1 flex items-center justify-center gap-1.5 rounded-md border border-red-200 hover:bg-red-50 dark:border-red-900/50 dark:hover:bg-red-500/10 active:bg-red-100 disabled:opacity-50 text-red-600 dark:text-red-400 py-2 text-sm font-semibold transition-colors"
                  >
                    <XCircle className="h-4 w-4" />
                    Reject
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="rounded-lg border border-dashed border-neutral-300 p-8 text-center text-sm text-neutral-400 dark:border-neutral-800">
              Select a resolution recommendation from the list to view original and revised clauses side-by-side with AI redline analysis.
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
