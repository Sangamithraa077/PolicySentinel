import { useState } from "react";
import { Loader2, Layers, ShieldAlert } from "lucide-react";

import { usePolicies } from "@/hooks/usePolicies";
import { useRelationships } from "@/hooks/useRelationships";
import type { Relationship } from "@/types/relationship";

export function RelationshipDashboardPage() {
  const [selectedType, setSelectedType] = useState("");
  const [selectedPolicyId, setSelectedPolicyId] = useState("");
  const [selectedRelationship, setSelectedRelationship] = useState<Relationship | null>(null);

  // 1. Fetch policies
  const policiesQuery = usePolicies();

  // 2. Fetch relationships for counts (limit 1000 to cover all)
  const allRelationshipsQuery = useRelationships({ limit: 1000 });

  // 3. Fetch filtered relationships list for view
  const relationshipsQuery = useRelationships({
    policyId: selectedPolicyId || undefined,
    relationshipType: selectedType || undefined,
  });

  const getRelationshipTypeBadge = (type: string) => {
    switch ((type || "").toUpperCase()) {
      case "CONFLICT":
        return "bg-red-50 text-red-700 ring-red-600/10 dark:bg-red-500/10 dark:text-red-400 dark:ring-red-500/20";
      case "REDUNDANT":
        return "bg-amber-50 text-amber-700 ring-amber-600/10 dark:bg-amber-500/10 dark:text-amber-400 dark:ring-amber-500/20";
      case "COMPLEMENTARY":
        return "bg-green-50 text-green-700 ring-green-600/10 dark:bg-green-500/10 dark:text-green-400 dark:ring-green-500/20";
      default:
        return "bg-blue-50 text-blue-700 ring-blue-600/10 dark:bg-blue-500/10 dark:text-blue-400 dark:ring-blue-500/20";
    }
  };

  const allItems = allRelationshipsQuery.data?.items ?? [];
  const totalCount = allItems.length;
  const conflictCount = allItems.filter((i) => i.relationship_type === "CONFLICT").length;
  const redundantCount = allItems.filter((i) => i.relationship_type === "REDUNDANT").length;
  const complementaryCount = allItems.filter((i) => i.relationship_type === "COMPLEMENTARY").length;
  const unrelatedCount = allItems.filter((i) => i.relationship_type === "UNRELATED").length;

  const isLoading = policiesQuery.isLoading || relationshipsQuery.isLoading;

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-foreground dark:text-neutral-100 flex items-center gap-2">
          <Layers className="h-6 w-6 text-brand-500" />
          AI Obligation Relationships
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-neutral-500">
          Classify and track how policy obligations relate to each other—detecting contradictions, redundancies, and complementary rules.
        </p>
      </div>

      {/* Grid of Counts/Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {/* Total card */}
        <div className="rounded-lg border border-border bg-surface p-4 shadow-sm dark:border-neutral-800 dark:bg-neutral-900/40">
          <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider block">Total Findings</span>
          <span className="text-2xl font-bold text-neutral-900 dark:text-white mt-1 block">{totalCount}</span>
        </div>
        {/* Conflicts card */}
        <div className="rounded-lg border border-border bg-surface p-4 shadow-sm dark:border-neutral-800 dark:bg-neutral-900/40">
          <span className="text-xs font-semibold text-red-500 uppercase tracking-wider block">Conflicts</span>
          <span className="text-2xl font-bold text-red-600 dark:text-red-400 mt-1 block">{conflictCount}</span>
        </div>
        {/* Redundant card */}
        <div className="rounded-lg border border-border bg-surface p-4 shadow-sm dark:border-neutral-800 dark:bg-neutral-900/40">
          <span className="text-xs font-semibold text-amber-500 uppercase tracking-wider block">Redundancies</span>
          <span className="text-2xl font-bold text-amber-600 dark:text-amber-400 mt-1 block">{redundantCount}</span>
        </div>
        {/* Complementary card */}
        <div className="rounded-lg border border-border bg-surface p-4 shadow-sm dark:border-neutral-800 dark:bg-neutral-900/40">
          <span className="text-xs font-semibold text-green-500 uppercase tracking-wider block">Complementary</span>
          <span className="text-2xl font-bold text-green-600 dark:text-green-400 mt-1 block">{complementaryCount}</span>
        </div>
        {/* Unrelated card */}
        <div className="rounded-lg border border-border bg-surface p-4 shadow-sm dark:border-neutral-800 dark:bg-neutral-900/40">
          <span className="text-xs font-semibold text-blue-500 uppercase tracking-wider block">Unrelated</span>
          <span className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1 block">{unrelatedCount}</span>
        </div>
      </div>

      {/* Filters and Table Splitting Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3 items-start">
        
        {/* Left Side: Filter inputs and lists */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            {/* Policy search filter */}
            <div className="relative flex-1">
              <select
                value={selectedPolicyId}
                onChange={(e) => {
                  setSelectedPolicyId(e.target.value);
                  setSelectedRelationship(null);
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

            {/* Relationship category filter */}
            <div className="relative flex-1">
              <select
                value={selectedType}
                onChange={(e) => {
                  setSelectedType(e.target.value);
                  setSelectedRelationship(null);
                }}
                className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-100"
              >
                <option value="">All Relationships</option>
                <option value="CONFLICT">Conflict</option>
                <option value="REDUNDANT">Redundant</option>
                <option value="COMPLEMENTARY">Complementary</option>
                <option value="UNRELATED">Unrelated</option>
              </select>
            </div>
          </div>

          {/* List Card */}
          <div className="overflow-hidden rounded-lg border border-border bg-surface shadow-sm dark:border-neutral-800 dark:bg-neutral-950">
            {isLoading ? (
              <div className="flex items-center justify-center p-12">
                <Loader2 className="h-8 w-8 animate-spin text-brand-500" />
              </div>
            ) : relationshipsQuery.isError ? (
              <div className="flex flex-col items-center justify-center p-12 text-center">
                <ShieldAlert className="h-10 w-10 text-red-500" />
                <p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">Failed to load relationships.</p>
                <button
                  onClick={() => relationshipsQuery.refetch()}
                  className="mt-4 text-xs font-semibold text-brand-600 hover:text-brand-500"
                >
                  Try Again
                </button>
              </div>
            ) : relationshipsQuery.data?.items.length === 0 ? (
              <div className="p-12 text-center text-sm text-neutral-500 dark:text-neutral-400">
                No relationship classifications found matching current criteria.
              </div>
            ) : (
              <div className="divide-y divide-border dark:divide-neutral-800">
                {relationshipsQuery.data?.items.map((rel) => (
                  <button
                    key={rel.id}
                    onClick={() => setSelectedRelationship(rel)}
                    className={`w-full flex items-start justify-between p-4 text-left hover:bg-neutral-50 dark:hover:bg-neutral-900/50 transition-colors ${
                      selectedRelationship?.id === rel.id ? "bg-brand-50/50 dark:bg-brand-500/5" : ""
                    }`}
                  >
                    <div className="flex flex-col gap-1 max-w-[80%]">
                      <div className="text-sm font-medium text-foreground dark:text-neutral-100 flex items-center gap-1.5 flex-wrap">
                        <span className="font-semibold text-neutral-400">[{rel.source_policy.title}]</span>
                        <span className="text-neutral-400 font-normal">vs</span>
                        <span className="font-semibold text-neutral-400">[{rel.target_policy.title}]</span>
                      </div>
                      <p className="text-xs text-neutral-500 truncate mt-1 italic">
                        {rel.explanation || "No explanation text recorded."}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset ${getRelationshipTypeBadge(
                          rel.relationship_type || ""
                        )}`}
                      >
                        {rel.relationship_type}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Side: Details View */}
        <div className="lg:col-span-1">
          {selectedRelationship ? (
            <div className="rounded-lg border border-border bg-surface p-5 shadow-sm dark:border-neutral-800 dark:bg-neutral-950 flex flex-col gap-6">
              
              {/* Classification Info */}
              <div>
                <h2 className="text-base font-semibold text-foreground dark:text-neutral-100">
                  Relationship Details
                </h2>
                <div className="mt-3 flex items-center justify-between flex-wrap gap-2">
                  <span
                    className={`inline-flex items-center rounded-md px-2.5 py-1 text-xs font-bold uppercase ring-1 ring-inset ${getRelationshipTypeBadge(
                      selectedRelationship.relationship_type || ""
                    )}`}
                  >
                    {selectedRelationship.relationship_type}
                  </span>
                  {selectedRelationship.confidence_score !== null && (
                    <div className="text-xs font-mono text-neutral-500">
                      Confidence: {(selectedRelationship.confidence_score * 100).toFixed(0)}%
                    </div>
                  )}
                </div>
              </div>

              {/* Side-by-side Obligations Comparison */}
              <div className="flex flex-col gap-4">
                
                {/* Obligation A (Existing) */}
                <div className="rounded-md border border-border p-3 bg-neutral-50/50 dark:bg-neutral-900/30 flex flex-col gap-2">
                  <span className="text-xs font-bold text-neutral-400 uppercase tracking-wider block">
                    Existing Obligation ({selectedRelationship.source_policy.title})
                  </span>
                  {selectedRelationship.source_obligation ? (
                    <div className="text-xs flex flex-col gap-1.5 mt-1 text-foreground dark:text-neutral-200">
                      <div><span className="font-semibold text-neutral-500">Subject:</span> {selectedRelationship.source_obligation.subject}</div>
                      <div><span className="font-semibold text-neutral-500">Action:</span> {selectedRelationship.source_obligation.action}</div>
                      <div><span className="font-semibold text-neutral-500">Object:</span> {selectedRelationship.source_obligation.object}</div>
                      <div>
                        <span className="font-semibold text-neutral-500">Modality:</span>{" "}
                        <span className="font-bold text-brand-600 dark:text-brand-400">
                          {selectedRelationship.source_obligation.modality}
                        </span>
                      </div>
                      {selectedRelationship.source_obligation.time_constraint && (
                        <div><span className="font-semibold text-neutral-500">Timing:</span> {selectedRelationship.source_obligation.time_constraint}</div>
                      )}
                    </div>
                  ) : (
                    <span className="text-xs text-neutral-400 italic">No matching source obligation mapped.</span>
                  )}
                </div>

                {/* Obligation B (New) */}
                <div className="rounded-md border border-border p-3 bg-neutral-50/50 dark:bg-neutral-900/30 flex flex-col gap-2">
                  <span className="text-xs font-bold text-neutral-400 uppercase tracking-wider block">
                    New Obligation ({selectedRelationship.target_policy.title})
                  </span>
                  {selectedRelationship.target_obligation ? (
                    <div className="text-xs flex flex-col gap-1.5 mt-1 text-foreground dark:text-neutral-200">
                      <div><span className="font-semibold text-neutral-500">Subject:</span> {selectedRelationship.target_obligation.subject}</div>
                      <div><span className="font-semibold text-neutral-500">Action:</span> {selectedRelationship.target_obligation.action}</div>
                      <div><span className="font-semibold text-neutral-500">Object:</span> {selectedRelationship.target_obligation.object}</div>
                      <div>
                        <span className="font-semibold text-neutral-500">Modality:</span>{" "}
                        <span className="font-bold text-brand-600 dark:text-brand-400">
                          {selectedRelationship.target_obligation.modality}
                        </span>
                      </div>
                      {selectedRelationship.target_obligation.time_constraint && (
                        <div><span className="font-semibold text-neutral-500">Timing:</span> {selectedRelationship.target_obligation.time_constraint}</div>
                      )}
                    </div>
                  ) : (
                    <span className="text-xs text-neutral-400 italic">No matching target obligation mapped.</span>
                  )}
                </div>

              </div>

              {/* AI Explanation Box */}
              <div className="flex flex-col gap-1.5">
                <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider">
                  AI Relationship Explanation
                </span>
                <p className="text-xs text-neutral-700 dark:text-neutral-300 leading-relaxed bg-surface/50 p-2.5 rounded border border-border italic">
                  {selectedRelationship.explanation || "No classification explanation generated."}
                </p>
              </div>

            </div>
          ) : (
            <div className="rounded-lg border border-dashed border-neutral-300 p-8 text-center text-sm text-neutral-400 dark:border-neutral-800">
              Select a relationship finding from the list to compare obligations side-by-side with AI explanation analysis.
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
