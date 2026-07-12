import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Loader2, AlertTriangle, Search, CheckCircle, Eye, RefreshCw } from "lucide-react";

import { usePolicies } from "@/hooks/usePolicies";
import { useConflicts, useUpdateConflictStatus } from "@/hooks/useConflicts";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { extractApiErrorMessage } from "@/utils/apiError";
import type { Conflict } from "@/types/conflict";

export function ConflictDashboardPage() {
  const { policyId } = useParams<{ policyId?: string }>();
  const navigate = useNavigate();

  const [searchInput, setSearchInput] = useState("");
  const debouncedSearch = useDebouncedValue(searchInput, 300);
  const [selectedSeverity, setSelectedSeverity] = useState("");
  const [selectedType, setSelectedType] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("");
  const [selectedConflict, setSelectedConflict] = useState<Conflict | null>(null);

  // 1. Fetch policies for filter
  const policiesQuery = usePolicies();

  // 2. Fetch conflicts list
  const conflictsQuery = useConflicts({
    policyId: policyId || undefined,
    severity: selectedSeverity || undefined,
    conflictType: selectedType || undefined,
    status: selectedStatus || undefined,
    search: debouncedSearch || undefined,
  });

  // 3. Status Mutation
  const updateStatusMutation = useUpdateConflictStatus();

  const handleStatusUpdate = async (conflictId: string, status: string) => {
    try {
      const updated = await updateStatusMutation.mutateAsync({ conflictId, status });
      setSelectedConflict(updated);
    } catch (err) {
      console.error("Failed to update status", err);
    }
  };

  const getSeverityBadgeClass = (severity: string) => {
    switch (severity.toLowerCase()) {
      case "high":
        return "bg-red-50 text-red-700 ring-red-600/10 dark:bg-red-500/10 dark:text-red-400 dark:ring-red-500/20";
      case "medium":
        return "bg-amber-50 text-amber-700 ring-amber-600/10 dark:bg-amber-500/10 dark:text-amber-400 dark:ring-amber-500/20";
      default:
        return "bg-blue-50 text-blue-700 ring-blue-600/10 dark:bg-blue-500/10 dark:text-blue-400 dark:ring-blue-500/20";
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status.toLowerCase()) {
      case "resolved":
        return "bg-green-50 text-green-700 ring-green-600/10 dark:bg-green-500/10 dark:text-green-400 dark:ring-green-500/20";
      case "reviewed":
        return "bg-purple-50 text-purple-700 ring-purple-600/10 dark:bg-purple-500/10 dark:text-purple-400 dark:ring-purple-500/20";
      default:
        return "bg-neutral-50 text-neutral-600 ring-neutral-500/10 dark:bg-neutral-500/10 dark:text-neutral-400 dark:ring-neutral-500/20";
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-semibold text-foreground dark:text-neutral-100">
        Conflict dashboard
      </h1>
      <p className="mt-2 max-w-2xl text-sm text-neutral-500">
        Analyze compliance gaps, contradictions, and redundancy warnings identified by AI semantic comparison across your policy documents.
      </p>

      {/* Policy Selector & Table Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3 mt-6">
        {/* Main List */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            {/* Search Input */}
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-neutral-400" />
              <input
                type="text"
                placeholder="Search conflicts..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                className="w-full rounded-md border border-border bg-surface pl-9 pr-3 py-2 text-sm text-foreground focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-100"
              />
            </div>

            {/* Policy Filter */}
            {policiesQuery.isSuccess && (
              <select
                value={policyId ?? ""}
                onChange={(e) =>
                  navigate(e.target.value ? `/conflicts/${e.target.value}` : "/conflicts")
                }
                className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-100 sm:w-44"
              >
                <option value="">All Policies</option>
                {policiesQuery.data.items.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.title}
                  </option>
                ))}
              </select>
            )}

            {/* Severity Filter */}
            <select
              value={selectedSeverity}
              onChange={(e) => setSelectedSeverity(e.target.value)}
              className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-100 sm:w-36"
            >
              <option value="">All Severities</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>

            {/* Status Filter */}
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-100 sm:w-36"
            >
              <option value="">All Statuses</option>
              <option value="open">Open</option>
              <option value="reviewed">Reviewed</option>
              <option value="resolved">Resolved</option>
            </select>
          </div>

          {/* Grid/Table Wrapper */}
          <div className="rounded-lg border border-border bg-surface overflow-hidden dark:border-neutral-800 dark:bg-neutral-900">
            {conflictsQuery.isPending && (
              <div className="flex flex-col items-center justify-center p-12 gap-2 text-sm text-neutral-500">
                <Loader2 className="h-6 w-6 animate-spin text-brand-600" />
                Loading detected conflicts...
              </div>
            )}

            {conflictsQuery.isError && (
              <div className="p-8 text-center text-sm text-red-600 dark:text-red-400">
                {extractApiErrorMessage(conflictsQuery.error, "Failed to load conflicts.")}
              </div>
            )}

            {conflictsQuery.isSuccess && (
              <>
                {conflictsQuery.data.items.length === 0 ? (
                  <div className="p-12 text-center text-sm text-neutral-500">
                    No compliance conflicts detected matching your criteria.
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-border bg-surface-muted/50 text-xs font-semibold text-neutral-500 dark:border-neutral-800 dark:bg-neutral-950/50 dark:text-neutral-400">
                          <th className="px-4 py-3">Conflict Type</th>
                          <th className="px-4 py-3">Source Policy</th>
                          <th className="px-4 py-3">Target Policy</th>
                          <th className="px-4 py-3 text-right">Similarity</th>
                          <th className="px-4 py-3">Severity</th>
                          <th className="px-4 py-3">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border dark:divide-neutral-800 text-sm">
                        {conflictsQuery.data.items.map((conflict) => (
                          <tr
                            key={conflict.id}
                            onClick={() => setSelectedConflict(conflict)}
                            className={`cursor-pointer hover:bg-surface-muted/65 transition-colors ${
                              selectedConflict?.id === conflict.id
                                ? "bg-brand-50/50 hover:bg-brand-50/60 dark:bg-brand-500/5 dark:hover:bg-brand-500/10"
                                : ""
                            }`}
                          >
                            <td className="px-4 py-3.5 font-medium text-foreground dark:text-neutral-200 capitalize">
                              {conflict.conflict_type}
                            </td>
                            <td className="px-4 py-3.5 text-neutral-600 dark:text-neutral-400 max-w-[150px] truncate">
                              {conflict.source_policy.title}
                            </td>
                            <td className="px-4 py-3.5 text-neutral-600 dark:text-neutral-400 max-w-[150px] truncate">
                              {conflict.target_policy.title}
                            </td>
                            <td className="px-4 py-3.5 text-right font-mono text-xs">
                              {Math.round(conflict.similarity_score * 100)}%
                            </td>
                            <td className="px-4 py-3.5">
                              <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${getSeverityBadgeClass(conflict.severity)}`}>
                                {conflict.severity}
                              </span>
                            </td>
                            <td className="px-4 py-3.5">
                              <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${getStatusBadgeClass(conflict.status)}`}>
                                {conflict.status}
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

        {/* Side Detail Panel */}
        <div className="lg:col-span-1 border border-border bg-surface rounded-lg p-5 dark:border-neutral-800 dark:bg-neutral-900 flex flex-col gap-5">
          {!selectedConflict ? (
            <div className="flex h-64 flex-col items-center justify-center gap-2 text-center text-sm text-neutral-500">
              <AlertTriangle className="h-8 w-8 text-neutral-300 dark:text-neutral-700" />
              Select a conflict from the list to view the side-by-side obligation comparison.
            </div>
          ) : (
            <div className="flex flex-col gap-5">
              <div>
                <h3 className="text-lg font-semibold text-foreground dark:text-neutral-100">
                  Conflict details
                </h3>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${getSeverityBadgeClass(selectedConflict.severity)}`}>
                    {selectedConflict.severity} severity
                  </span>
                  <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${getStatusBadgeClass(selectedConflict.status)}`}>
                    {selectedConflict.status}
                  </span>
                </div>
              </div>

              {/* Status Update Actions */}
              <div className="flex gap-2">
                <button
                  onClick={() => handleStatusUpdate(selectedConflict.id, "Reviewed")}
                  disabled={updateStatusMutation.isPending}
                  className="flex-1 flex items-center justify-center gap-1.5 rounded-md border border-border bg-surface px-3 py-1.5 text-xs font-medium text-neutral-700 hover:bg-surface-muted focus:outline-none dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-200 dark:hover:bg-neutral-800"
                >
                  <Eye className="h-3.5 w-3.5" />
                  Mark Reviewed
                </button>
                <button
                  onClick={() => handleStatusUpdate(selectedConflict.id, "Resolved")}
                  disabled={updateStatusMutation.isPending}
                  className="flex-1 flex items-center justify-center gap-1.5 rounded-md bg-brand-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-brand-700 focus:outline-none dark:bg-brand-500 dark:hover:bg-brand-600"
                >
                  <CheckCircle className="h-3.5 w-3.5" />
                  Mark Resolved
                </button>
              </div>

              <hr className="border-border dark:border-neutral-800" />

              {/* AI Explanation */}
              <div>
                <h4 className="text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-2">
                  AI analysis explanation
                </h4>
                <p className="text-sm text-neutral-700 dark:text-neutral-300 leading-relaxed bg-surface-muted/40 p-3 rounded border border-border/80 dark:border-neutral-800/80">
                  {selectedConflict.ai_explanation || "No explanation provided."}
                </p>
              </div>

              {/* Side-by-side obligation fields */}
              <div>
                <h4 className="text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-3">
                  Side-by-Side Obligation Comparison
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2 gap-4">
                  {/* Source Obligation */}
                  <div className="border border-border p-3.5 rounded bg-surface-muted/20 dark:border-neutral-800 dark:bg-neutral-950/20">
                    <h5 className="text-xs font-bold uppercase text-neutral-500 mb-2 truncate">
                      Source: {selectedConflict.source_policy.title}
                    </h5>
                    {selectedConflict.source_obligation ? (
                      <div className="space-y-2 text-xs">
                        <div>
                          <span className="text-neutral-400 block font-semibold uppercase tracking-wider">Subject</span>
                          <span className="text-foreground dark:text-neutral-200">{selectedConflict.source_obligation.subject}</span>
                        </div>
                        <div>
                          <span className="text-neutral-400 block font-semibold uppercase tracking-wider">Action</span>
                          <span className="text-foreground dark:text-neutral-200">{selectedConflict.source_obligation.action} {selectedConflict.source_obligation.object}</span>
                        </div>
                        <div className="grid grid-cols-2 gap-1">
                          <div>
                            <span className="text-neutral-400 block font-semibold uppercase tracking-wider">Modality</span>
                            <span className="text-foreground dark:text-neutral-200 font-medium">{selectedConflict.source_obligation.modality}</span>
                          </div>
                          <div>
                            <span className="text-neutral-400 block font-semibold uppercase tracking-wider">Category</span>
                            <span className="text-foreground dark:text-neutral-200">{selectedConflict.source_obligation.compliance_category}</span>
                          </div>
                        </div>
                        {selectedConflict.source_obligation.time_constraint && (
                          <div>
                            <span className="text-neutral-400 block font-semibold uppercase tracking-wider">Time Limit</span>
                            <span className="text-foreground dark:text-neutral-200">{selectedConflict.source_obligation.time_constraint}</span>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="text-xs text-neutral-500 italic p-2 border border-dashed border-border dark:border-neutral-800 text-center rounded">
                        Not present in source version.
                      </div>
                    )}
                  </div>

                  {/* Target Obligation */}
                  <div className="border border-border p-3.5 rounded bg-surface-muted/20 dark:border-neutral-800 dark:bg-neutral-950/20">
                    <h5 className="text-xs font-bold uppercase text-neutral-500 mb-2 truncate">
                      Target: {selectedConflict.target_policy.title}
                    </h5>
                    {selectedConflict.target_obligation ? (
                      <div className="space-y-2 text-xs">
                        <div>
                          <span className="text-neutral-400 block font-semibold uppercase tracking-wider">Subject</span>
                          <span className="text-foreground dark:text-neutral-200">{selectedConflict.target_obligation.subject}</span>
                        </div>
                        <div>
                          <span className="text-neutral-400 block font-semibold uppercase tracking-wider">Action</span>
                          <span className="text-foreground dark:text-neutral-200">{selectedConflict.target_obligation.action} {selectedConflict.target_obligation.object}</span>
                        </div>
                        <div className="grid grid-cols-2 gap-1">
                          <div>
                            <span className="text-neutral-400 block font-semibold uppercase tracking-wider">Modality</span>
                            <span className="text-foreground dark:text-neutral-200 font-medium">{selectedConflict.target_obligation.modality}</span>
                          </div>
                          <div>
                            <span className="text-neutral-400 block font-semibold uppercase tracking-wider">Category</span>
                            <span className="text-foreground dark:text-neutral-200">{selectedConflict.target_obligation.compliance_category}</span>
                          </div>
                        </div>
                        {selectedConflict.target_obligation.time_constraint && (
                          <div>
                            <span className="text-neutral-400 block font-semibold uppercase tracking-wider">Time Limit</span>
                            <span className="text-foreground dark:text-neutral-200">{selectedConflict.target_obligation.time_constraint}</span>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="text-xs text-neutral-500 italic p-2 border border-dashed border-border dark:border-neutral-800 text-center rounded">
                        Not present in target version.
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ConflictDashboardPage;
