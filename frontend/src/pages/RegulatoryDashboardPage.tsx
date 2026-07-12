import { useState } from "react";
import { Loader2, ShieldCheck, AlertOctagon, HelpCircle, FileText, CheckCircle2, ChevronRight, BarChart3, Filter } from "lucide-react";

import { usePolicies } from "@/hooks/usePolicies";
import { useRegulatoryMappings, usePolicyHealthScore, useRegulatoryFrameworks } from "@/hooks/useRegulatoryMappings";
import { getPolicyHealthScore } from "@/services/regulatoryMappingService";
import { useQuery } from "@tanstack/react-query";

export function RegulatoryDashboardPage() {
  const [selectedPolicyId, setSelectedPolicyId] = useState<string>("");
  const [selectedFrameworkName, setSelectedFrameworkName] = useState<string>("");
  const [selectedGrade, setSelectedGrade] = useState<string>("");
  const [selectedMappingId, setSelectedMappingId] = useState<string>("");

  // 1. Fetch policies
  const policiesQuery = usePolicies();
  const policies = policiesQuery.data?.items ?? [];

  // 2. Fetch all mappings (up to 1000) for distribution calculations
  const allMappingsQuery = useRegulatoryMappings({ limit: 1000 });
  const allMappings = allMappingsQuery.data?.items ?? [];

  // 3. Fetch regulatory frameworks
  const frameworksQuery = useRegulatoryFrameworks();
  const frameworks = frameworksQuery.data ?? [];

  // 4. Fetch health score for selected policy or default to first policy if none selected
  const defaultPolicyId = selectedPolicyId || (policies.length > 0 ? policies[0].id : undefined);
  const healthQuery = usePolicyHealthScore(defaultPolicyId);
  const health = healthQuery.data;

  // 5. Pre-calculate health scores for all policies to support filtering by Grade
  const allHealthScoresQuery = useQuery({
    queryKey: ["all-policies-health", policies.map((p) => p.id).join(",")],
    queryFn: async () => {
      const results: Record<string, { score: number; grade: string }> = {};
      for (const p of policies) {
        try {
          const res = await getPolicyHealthScore(p.id);
          results[p.id] = { score: res.score, grade: res.grade };
        } catch (e) {
          results[p.id] = { score: 100, grade: "A" };
        }
      }
      return results;
    },
    enabled: policies.length > 0,
  });
  const allHealthScores = allHealthScoresQuery.data ?? {};

  // Filtered policies list based on Grade selection
  const filteredPolicies = policies.filter((p) => {
    if (!selectedGrade) return true;
    const policyGrade = allHealthScores[p.id]?.grade ?? "";
    return policyGrade === selectedGrade;
  });

  // Active mappings list based on filters
  const filteredMappings = allMappings.filter((m) => {
    if (selectedPolicyId && m.policy_id !== selectedPolicyId) return false;
    if (selectedFrameworkName && m.framework_name !== selectedFrameworkName) return false;
    if (selectedGrade) {
      // Mapping belongs to a policy with selected grade
      const policyGrade = allHealthScores[m.policy_id]?.grade ?? "";
      if (policyGrade !== selectedGrade) return false;
    }
    return true;
  });

  // Calculate coverage stats
  const totalCount = allMappings.length;
  const mappedCount = allMappings.filter((m) => m.framework_name !== "NONE").length;
  const missingCount = allMappings.filter((m) => m.framework_name === "NONE").length;
  const coveragePercent = totalCount > 0 ? (mappedCount / totalCount) * 100 : 100;

  // Framework distribution
  const frameworkCounts: Record<string, number> = {};
  allMappings.forEach((m) => {
    if (m.framework_name !== "NONE") {
      frameworkCounts[m.framework_name] = (frameworkCounts[m.framework_name] || 0) + 1;
    }
  });

  const getGradeBadgeColor = (grade: string) => {
    switch (grade) {
      case "A":
        return "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-400 border-emerald-500/20";
      case "B":
        return "bg-teal-100 text-teal-800 dark:bg-teal-950/30 dark:text-teal-400 border-teal-500/20";
      case "C":
        return "bg-amber-100 text-amber-800 dark:bg-amber-950/30 dark:text-amber-400 border-amber-500/20";
      case "D":
        return "bg-orange-100 text-orange-800 dark:bg-orange-950/30 dark:text-orange-400 border-orange-500/20";
      case "F":
        return "bg-red-100 text-red-800 dark:bg-red-950/30 dark:text-red-400 border-red-500/20";
      default:
        return "bg-neutral-100 text-neutral-800 dark:bg-neutral-900 dark:text-neutral-400 border-neutral-700/20";
    }
  };

  const selectedMapping = allMappings.find((m) => m.id === selectedMappingId);

  return (
    <div className="flex flex-col gap-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-semibold text-foreground dark:text-neutral-100 flex items-center gap-2">
          <ShieldCheck className="h-6 w-6 text-brand-500" />
          Regulatory Compliance Dashboard
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-neutral-500">
          Verify corporate policy alignment with international standards GDPR, ISO 27001, SEBI, and RBI.
        </p>
      </div>

      {/* Dynamic Filters panel */}
      <div className="rounded-lg border border-border bg-surface p-4 shadow-sm dark:border-neutral-800 dark:bg-neutral-900/40 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-2 text-sm font-semibold text-neutral-400">
          <Filter className="h-4 w-4 text-brand-500" />
          <span>Dashboard Filters</span>
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 flex-1 max-w-3xl">
          {/* Policy filter */}
          <select
            value={selectedPolicyId}
            onChange={(e) => {
              setSelectedPolicyId(e.target.value);
              setSelectedMappingId("");
            }}
            className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-foreground focus:border-brand-500 focus:outline-none dark:border-neutral-700 dark:bg-neutral-900"
          >
            <option value="">All Policies</option>
            {filteredPolicies.map((p) => (
              <option key={p.id} value={p.id}>
                {p.title}
              </option>
            ))}
          </select>

          {/* Framework filter */}
          <select
            value={selectedFrameworkName}
            onChange={(e) => {
              setSelectedFrameworkName(e.target.value);
              setSelectedMappingId("");
            }}
            className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-foreground focus:border-brand-500 focus:outline-none dark:border-neutral-700 dark:bg-neutral-900"
          >
            <option value="">All Frameworks</option>
            {frameworks.map((fw) => (
              <option key={fw.id} value={fw.name}>
                {fw.name} ({fw.issuing_body || "External"})
              </option>
            ))}
            <option value="NONE">Unmapped (NONE)</option>
          </select>

          {/* Grade filter */}
          <select
            value={selectedGrade}
            onChange={(e) => {
              setSelectedGrade(e.target.value);
              setSelectedPolicyId("");
              setSelectedMappingId("");
            }}
            className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-foreground focus:border-brand-500 focus:outline-none dark:border-neutral-700 dark:bg-neutral-900"
          >
            <option value="">All Grades</option>
            <option value="A">Grade A (90-100)</option>
            <option value="B">Grade B (80-89)</option>
            <option value="C">Grade C (70-79)</option>
            <option value="D">Grade D (60-69)</option>
            <option value="F">Grade F (&lt; 60)</option>
          </select>
        </div>
      </div>

      {/* Metrics Summary Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Policy Health Score */}
        <div className="rounded-lg border border-border bg-surface p-4 shadow-sm dark:border-neutral-800 dark:bg-neutral-900/40">
          <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider block">Policy Health Score</span>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-3xl font-extrabold text-neutral-900 dark:text-white">
              {health ? health.score : "N/A"}
            </span>
            <span className="text-xs text-neutral-400">/ 100</span>
          </div>
        </div>

        {/* Compliance Grade */}
        <div className="rounded-lg border border-border bg-surface p-4 shadow-sm dark:border-neutral-800 dark:bg-neutral-900/40">
          <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider block">Compliance Grade</span>
          <div className="mt-2.5">
            <span className={`inline-flex items-center rounded-md px-3 py-1 text-sm font-semibold border ${getGradeBadgeColor(health?.grade ?? "")}`}>
              Grade {health ? health.grade : "N/A"}
            </span>
          </div>
        </div>

        {/* Regulatory Coverage */}
        <div className="rounded-lg border border-border bg-surface p-4 shadow-sm dark:border-neutral-800 dark:bg-neutral-900/40">
          <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider block">Regulatory Coverage</span>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-3xl font-extrabold text-neutral-900 dark:text-white">
              {coveragePercent.toFixed(1)}%
            </span>
            <span className="text-xs text-neutral-400">mapped</span>
          </div>
        </div>

        {/* Missing Mappings */}
        <div className="rounded-lg border border-border bg-surface p-4 shadow-sm dark:border-neutral-800 dark:bg-neutral-900/40">
          <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider block">Missing Mappings</span>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-3xl font-extrabold text-red-600 dark:text-red-400">
              {missingCount}
            </span>
            <span className="text-xs text-neutral-400">obligations unmapped</span>
          </div>
        </div>
      </div>

      {/* Grid containing details, risks, and framework distributions */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3 items-start">
        
        {/* Left 2 Columns: Framework distribution and mappings table */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          
          {/* Framework Distribution */}
          <div className="rounded-lg border border-border bg-surface p-5 shadow-sm dark:border-neutral-800 dark:bg-neutral-950">
            <h2 className="text-sm font-bold text-foreground dark:text-neutral-100 flex items-center gap-1.5 uppercase tracking-wider">
              <BarChart3 className="h-4 w-4 text-brand-500" />
              Framework Distribution
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4">
              {["GDPR", "ISO 27001", "RBI", "SEBI"].map((fw) => {
                const count = frameworkCounts[fw] || 0;
                return (
                  <div key={fw} className="rounded-md bg-neutral-50 p-3.5 dark:bg-neutral-900/30 border border-border dark:border-neutral-800">
                    <span className="text-xs font-bold text-neutral-400 block">{fw}</span>
                    <span className="text-xl font-bold text-neutral-900 dark:text-white mt-1 block">{count}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Mapped Obligations List */}
          <div className="rounded-lg border border-border bg-surface p-5 shadow-sm dark:border-neutral-800 dark:bg-neutral-950 flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-foreground dark:text-neutral-100 uppercase tracking-wider block">
                Mapped Compliance Inventory ({filteredMappings.length})
              </h2>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-left text-xs">
                <thead>
                  <tr className="border-b border-border dark:border-neutral-800 text-neutral-400 font-semibold uppercase">
                    <th className="py-2.5">Framework</th>
                    <th className="py-2.5">Clause Reference</th>
                    <th className="py-2.5">Compliance Score</th>
                    <th className="py-2.5">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border dark:divide-neutral-800 text-neutral-300">
                  {allMappingsQuery.isLoading ? (
                    <tr>
                      <td colSpan={4} className="py-8 text-center">
                        <Loader2 className="h-6 w-6 animate-spin text-brand-500 mx-auto" />
                      </td>
                    </tr>
                  ) : filteredMappings.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="py-8 text-center text-neutral-500">
                        No mappings match selected criteria.
                      </td>
                    </tr>
                  ) : (
                    filteredMappings.map((m) => (
                      <tr 
                        key={m.id}
                        onClick={() => setSelectedMappingId(m.id)}
                        className={`hover:bg-neutral-50 dark:hover:bg-neutral-900/40 cursor-pointer transition-colors ${
                          selectedMappingId === m.id ? "bg-brand-50/50 dark:bg-brand-500/5" : ""
                        }`}
                      >
                        <td className="py-3 font-semibold text-foreground dark:text-white">
                          <span className={`inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-bold ${
                            m.framework_name === "NONE" 
                              ? "bg-red-50 text-red-700 ring-1 ring-inset ring-red-600/10 dark:bg-red-950/20 dark:text-red-400"
                              : "bg-blue-50 text-blue-700 ring-1 ring-inset ring-blue-600/10 dark:bg-blue-950/20 dark:text-blue-400"
                          }`}>
                            {m.framework_name}
                          </span>
                        </td>
                        <td className="py-3 font-mono text-neutral-400">{m.clause_number}</td>
                        <td className="py-3 font-semibold text-brand-600 dark:text-brand-400">
                          {m.confidence_score !== 0 ? `${(m.confidence_score * 100).toFixed(0)}%` : "N/A"}
                        </td>
                        <td className="py-3">
                          <button className="text-brand-500 hover:text-brand-600 font-semibold inline-flex items-center gap-0.5">
                            Details <ChevronRight className="h-3.5 w-3.5" />
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

          </div>

        </div>

        {/* Right 1 Column: Health Score Summary Risks & Mappings detailed view */}
        <div className="lg:col-span-1 flex flex-col gap-6">
          
          {/* Top Compliance Risks */}
          {health && (
            <div className="rounded-lg border border-border bg-surface p-5 shadow-sm dark:border-neutral-800 dark:bg-neutral-950 flex flex-col gap-3">
              <h2 className="text-sm font-bold text-foreground dark:text-neutral-100 flex items-center gap-1.5 uppercase tracking-wider">
                <AlertOctagon className="h-4 w-4 text-red-500" />
                Top Compliance Risks
              </h2>
              {health.risk_factors.length === 0 ? (
                <div className="text-xs text-neutral-500 text-center py-4">
                  No critical compliance risk factors identified.
                </div>
              ) : (
                <ul className="flex flex-col gap-2.5 mt-2">
                  {health.risk_factors.map((risk, idx) => (
                    <li key={idx} className="text-xs text-neutral-700 dark:text-neutral-300 flex items-start gap-2 bg-red-50/10 border border-red-500/10 p-2.5 rounded-md">
                      <span className="w-1.5 h-1.5 rounded-full bg-red-500 mt-1.5 flex-shrink-0" />
                      <span>{risk}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {/* Detailed Mapping Selector Box */}
          {selectedMapping ? (
            <div className="rounded-lg border border-border bg-surface p-5 shadow-sm dark:border-neutral-800 dark:bg-neutral-950 flex flex-col gap-5">
              <div>
                <h3 className="text-sm font-bold text-foreground dark:text-neutral-100">
                  Regulatory Mapping Details
                </h3>
                <span className="text-[10px] text-neutral-400 block mt-1">ID: {selectedMapping.id}</span>
              </div>

              <div className="border-t border-b border-border py-3 flex flex-col gap-2.5">
                <div className="text-xs">
                  <span className="font-semibold text-neutral-400 uppercase tracking-wider block text-[10px]">Framework</span>
                  <span className="text-foreground font-bold mt-0.5 block">{selectedMapping.framework_name}</span>
                </div>
                <div className="text-xs">
                  <span className="font-semibold text-neutral-400 uppercase tracking-wider block text-[10px]">Clause / regulation</span>
                  <span className="text-foreground font-mono mt-0.5 block">{selectedMapping.clause_number}</span>
                </div>
                <div className="text-xs">
                  <span className="font-semibold text-neutral-400 uppercase tracking-wider block text-[10px]">Confidence score</span>
                  <span className="text-brand-600 font-bold mt-0.5 block">{(selectedMapping.confidence_score * 100).toFixed(0)}%</span>
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider">
                  Mapping explanation & reasoning
                </span>
                <p className="text-xs text-neutral-700 dark:text-neutral-300 leading-relaxed bg-surface/50 p-2.5 rounded border border-border italic">
                  {selectedMapping.ai_explanation || "No mapping explanation recorded."}
                </p>
              </div>

            </div>
          ) : (
            <div className="rounded-lg border border-dashed border-neutral-300 p-8 text-center text-sm text-neutral-400 dark:border-neutral-800">
              Select an item from the mapped compliance inventory to view mapping explanation, confidence score, and regulation details.
            </div>
          )}

        </div>

      </div>

    </div>
  );
}
