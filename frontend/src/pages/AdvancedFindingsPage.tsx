import { useState } from "react";
import { Loader2, FileWarning, ShieldCheck, Clock } from "lucide-react";

import { usePolicies } from "@/hooks/usePolicies";
import { useFindings } from "@/hooks/useFindings";
import type { Finding } from "@/types/finding";

export function AdvancedFindingsPage() {
  const [selectedTab, setSelectedTab] = useState<"all" | "temporal" | "strength" | "stale">("all");
  const [selectedPolicyId, setSelectedPolicyId] = useState("");
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);

  // 1. Fetch policies
  const policiesQuery = usePolicies();

  // 2. Fetch all findings (limit 1000) for summary tallying
  const allFindingsQuery = useFindings({ limit: 1000 });

  // 3. Fetch list filterable by current query state
  const findingsQuery = useFindings({
    policyId: selectedPolicyId || undefined,
    findingType: selectedTab === "all" ? undefined : selectedTab,
  });

  const allItems = allFindingsQuery.data?.items ?? [];
  const totalCount = allItems.length;
  
  const temporalCount = allItems.filter(
    (i) => i.temporal_conflict && i.temporal_conflict !== "none"
  ).length;

  const strengthCount = allItems.filter(
    (i) => i.strength_conflict && i.strength_conflict !== "NONE"
  ).length;

  const staleCount = allItems.filter(
    (i) => i.staleness_status === "Outdated" || i.staleness_status === "Review Required"
  ).length;

  const isLoading = policiesQuery.isLoading || findingsQuery.isLoading;

  const getRecommendedAction = (finding: Finding): string => {
    if (finding.staleness_status === "Outdated" || finding.staleness_status === "Review Required") {
      return "ACTION REQUIRED: Trigger a revision review cycle for the policy. Verify effective dates and verify if a newer revision has been published.";
    }
    if (finding.temporal_conflict && finding.temporal_conflict !== "none") {
      return "RESOLVE MISMATCH: Sync the deadline constraints. Verify if the target or source policy requires adjustment to matching terms.";
    }
    if (finding.strength_conflict && finding.strength_conflict !== "NONE") {
      return "REVIEW MODALITY: Assess modal obligation differences. Ensure that guideline/permissive modalities ('Should'/'May') do not compromise corporate mandatory controls ('Must'/'Shall').";
    }
    return "MONITOR: No severe anomalies detected. Acknowledge and mark finding as reviewed.";
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-foreground dark:text-neutral-100 flex items-center gap-2">
          <FileWarning className="h-6 w-6 text-brand-500" />
          Advanced Findings Dashboard
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-neutral-500">
          Conduct deeper analysis of time-based conflicts, modality strength weaknesses, and policy lifecycle staleness.
        </p>
      </div>

      {/* Grid of Counts/Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Total card */}
        <div 
          onClick={() => { setSelectedTab("all"); setSelectedFinding(null); }}
          className={`rounded-lg border p-4 shadow-sm cursor-pointer transition-all ${
            selectedTab === "all" ? "border-brand-500 bg-brand-50/10 dark:bg-brand-500/5" : "border-border bg-surface dark:border-neutral-800 dark:bg-neutral-900/40"
          }`}
        >
          <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider block">Overall Summary</span>
          <span className="text-2xl font-bold text-neutral-900 dark:text-white mt-1 block">{totalCount}</span>
        </div>
        {/* Temporal card */}
        <div 
          onClick={() => { setSelectedTab("temporal"); setSelectedFinding(null); }}
          className={`rounded-lg border p-4 shadow-sm cursor-pointer transition-all ${
            selectedTab === "temporal" ? "border-amber-500 bg-amber-50/10 dark:bg-amber-500/5" : "border-border bg-surface dark:border-neutral-800 dark:bg-neutral-900/40"
          }`}
        >
          <span className="text-xs font-semibold text-amber-500 uppercase tracking-wider block">Temporal Conflicts</span>
          <span className="text-2xl font-bold text-amber-600 dark:text-amber-400 mt-1 block">{temporalCount}</span>
        </div>
        {/* Strength card */}
        <div 
          onClick={() => { setSelectedTab("strength"); setSelectedFinding(null); }}
          className={`rounded-lg border p-4 shadow-sm cursor-pointer transition-all ${
            selectedTab === "strength" ? "border-purple-500 bg-purple-50/10 dark:bg-purple-500/5" : "border-border bg-surface dark:border-neutral-800 dark:bg-neutral-900/40"
          }`}
        >
          <span className="text-xs font-semibold text-purple-500 uppercase tracking-wider block">Strength Conflicts</span>
          <span className="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-1 block">{strengthCount}</span>
        </div>
        {/* Stale card */}
        <div 
          onClick={() => { setSelectedTab("stale"); setSelectedFinding(null); }}
          className={`rounded-lg border p-4 shadow-sm cursor-pointer transition-all ${
            selectedTab === "stale" ? "border-red-500 bg-red-50/10 dark:bg-red-500/5" : "border-border bg-surface dark:border-neutral-800 dark:bg-neutral-900/40"
          }`}
        >
          <span className="text-xs font-semibold text-red-500 uppercase tracking-wider block">Stale Policies</span>
          <span className="text-2xl font-bold text-red-600 dark:text-red-400 mt-1 block">{staleCount}</span>
        </div>
      </div>

      {/* Table grid layout */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3 items-start">
        
        {/* Main List Column */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            {/* Policy Filter */}
            <div className="relative flex-1">
              <select
                value={selectedPolicyId}
                onChange={(e) => {
                  setSelectedPolicyId(e.target.value);
                  setSelectedFinding(null);
                }}
                className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-100"
              >
                <option value="">All Policies</option>
                {policiesQuery.data?.items.map((pol) => (
                  <option key={pol.id} value={pol.id}>
                    {pol.title}
                  </option>
                ))}
              </select>
            </div>
            {/* Active tab summary badge */}
            <div className="text-xs font-medium text-neutral-400">
              Showing active selection: <span className="font-semibold text-foreground capitalize">{selectedTab}</span>
            </div>
          </div>

          <div className="overflow-hidden rounded-lg border border-border bg-surface shadow-sm dark:border-neutral-800 dark:bg-neutral-950">
            {isLoading ? (
              <div className="flex items-center justify-center p-12">
                <Loader2 className="h-8 w-8 animate-spin text-brand-500" />
              </div>
            ) : findingsQuery.data?.items.length === 0 ? (
              <div className="p-12 text-center text-sm text-neutral-500 dark:text-neutral-400">
                No advanced findings found matching current filter query.
              </div>
            ) : (
              <div className="divide-y divide-border dark:divide-neutral-800">
                {findingsQuery.data?.items.map((find) => (
                  <button
                    key={find.id}
                    onClick={() => setSelectedFinding(find)}
                    className={`w-full flex items-start justify-between p-4 text-left hover:bg-neutral-50 dark:hover:bg-neutral-900/50 transition-colors ${
                      selectedFinding?.id === find.id ? "bg-brand-50/50 dark:bg-brand-500/5" : ""
                    }`}
                  >
                    <div className="flex flex-col gap-1 max-w-[80%]">
                      <div className="text-sm font-semibold text-foreground dark:text-neutral-100 flex items-center gap-1.5 flex-wrap">
                        <span>{find.source_policy.title}</span>
                        <span className="text-neutral-400 font-normal">vs</span>
                        <span>{find.target_policy.title}</span>
                      </div>
                      <p className="text-xs text-neutral-400 truncate mt-1">
                        {find.explanation || find.ai_explanation || "No explanation text recorded."}
                      </p>
                      
                      {/* Sub-badge indicators */}
                      <div className="flex items-center gap-2 mt-2">
                        {find.temporal_conflict && find.temporal_conflict !== "none" && (
                          <span className="inline-flex items-center gap-0.5 rounded bg-amber-50 px-1.5 py-0.5 text-[10px] font-medium text-amber-700 ring-1 ring-inset ring-amber-600/10 dark:bg-amber-500/10 dark:text-amber-400">
                            <Clock className="h-3 w-3" /> Temporal
                          </span>
                        )}
                        {find.strength_conflict && find.strength_conflict !== "NONE" && (
                          <span className="inline-flex items-center gap-0.5 rounded bg-purple-50 px-1.5 py-0.5 text-[10px] font-medium text-purple-700 ring-1 ring-inset ring-purple-600/10 dark:bg-purple-500/10 dark:text-purple-400">
                            <ShieldCheck className="h-3 w-3" /> Strength ({find.strength_conflict})
                          </span>
                        )}
                        {find.staleness_status && find.staleness_status !== "Current" && (
                          <span className="inline-flex items-center gap-0.5 rounded bg-red-50 px-1.5 py-0.5 text-[10px] font-medium text-red-700 ring-1 ring-inset ring-red-600/10 dark:bg-red-500/10 dark:text-red-400">
                            Stale: {find.staleness_status}
                          </span>
                        )}
                      </div>

                    </div>
                    <div className="text-xs font-mono text-neutral-400">
                      Severity: <span className="font-semibold">{find.severity}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

        </div>

        {/* Details View Column */}
        <div className="lg:col-span-1">
          {selectedFinding ? (
            <div className="rounded-lg border border-border bg-surface p-5 shadow-sm dark:border-neutral-800 dark:bg-neutral-950 flex flex-col gap-6">
              
              {/* Finding Title & Confidence */}
              <div>
                <h2 className="text-base font-semibold text-foreground dark:text-neutral-100">
                  Analysis Details
                </h2>
                <div className="mt-3 flex items-center justify-between flex-wrap gap-2 text-xs">
                  <div className="flex items-center gap-1.5">
                    <span className="text-neutral-400 font-normal">Confidence Level:</span>
                    <span className="font-bold text-brand-600 dark:text-brand-400">
                      {selectedFinding.confidence_score !== null 
                        ? `${(selectedFinding.confidence_score * 100).toFixed(0)}%` 
                        : "N/A"}
                    </span>
                  </div>
                  <span className="text-neutral-400">Status: {selectedFinding.status}</span>
                </div>
              </div>

              {/* Policies Involved */}
              <div className="border-t border-b border-border py-3 flex flex-col gap-1.5">
                <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider block">
                  Policies Involved
                </span>
                <div className="text-xs flex flex-col gap-1">
                  <div><span className="font-semibold text-neutral-500">Source Policy:</span> {selectedFinding.source_policy.title}</div>
                  <div><span className="font-semibold text-neutral-500">Target Policy:</span> {selectedFinding.target_policy.title}</div>
                </div>
              </div>

              {/* Advanced Parameters Metadata */}
              {selectedFinding.detected_parameters && (
                <div className="rounded-md border border-border p-3 bg-neutral-50/50 dark:bg-neutral-900/30 flex flex-col gap-2">
                  <span className="text-xs font-bold text-neutral-400 uppercase tracking-wider block">
                    Detected Comparison Parameters
                  </span>
                  <div className="text-[11px] font-mono text-neutral-600 dark:text-neutral-300 flex flex-col gap-1 leading-normal">
                    {Object.entries(JSON.parse(selectedFinding.detected_parameters)).map(([key, val]) => (
                      <div key={key} className="truncate">
                        <span className="font-semibold text-neutral-400">{key}:</span> {val ? String(val) : "None"}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* AI Explanation Box */}
              <div className="flex flex-col gap-1.5">
                <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider">
                  AI Compliance Explanation
                </span>
                <p className="text-xs text-neutral-700 dark:text-neutral-300 leading-relaxed bg-surface/50 p-2.5 rounded border border-border italic">
                  {selectedFinding.explanation || selectedFinding.ai_explanation || "No explanation text recorded."}
                </p>
              </div>

              {/* Recommended Action */}
              <div className="rounded-md border border-brand-100 bg-brand-50/10 p-3.5 dark:border-brand-500/20 dark:bg-brand-500/5">
                <span className="text-xs font-bold text-brand-700 uppercase tracking-wider block dark:text-brand-300">
                  Recommended Mitigation
                </span>
                <p className="text-xs text-neutral-700 dark:text-neutral-300 mt-1.5 leading-relaxed">
                  {getRecommendedAction(selectedFinding)}
                </p>
              </div>

            </div>
          ) : (
            <div className="rounded-lg border border-dashed border-neutral-300 p-8 text-center text-sm text-neutral-400 dark:border-neutral-800">
              Select an advanced compliance finding from the list to display details, metadata parameters, and recommended actions.
            </div>
          )}
        </div>

      </div>

    </div>
  );
}
