import { useState } from "react";
import {
  FileText, Shield, AlertTriangle, CheckCircle2, Sparkles, List,
  TrendingDown, Activity, Loader2, RefreshCw, FileDown
} from "lucide-react";

import { usePolicies } from "@/hooks/usePolicies";
import { useExecutiveSummary, useComplianceAuditLogs } from "@/hooks/useComplianceDashboard";
import { useWorkspace } from "@/hooks/useWorkspace";
import { API_BASE_URL } from "@/services/apiClient";

const RELATIVE_TIME_UNITS: [Intl.RelativeTimeFormatUnit, number][] = [
  ["year", 31536000],
  ["month", 2592000],
  ["day", 86400],
  ["hour", 3600],
  ["minute", 60],
];
const relativeTimeFormatter = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" });

/** "2 hours ago" instead of a full locale timestamp — the exact time is
 * still available on hover via the cell's title attribute. */
function formatRelativeTime(iso: string): string {
  const seconds = (new Date(iso).getTime() - Date.now()) / 1000;
  for (const [unit, secondsInUnit] of RELATIVE_TIME_UNITS) {
    if (Math.abs(seconds) >= secondsInUnit) {
      return relativeTimeFormatter.format(Math.round(seconds / secondsInUnit), unit);
    }
  }
  return relativeTimeFormatter.format(Math.round(seconds), "second");
}

export function ExecutiveDashboardPage() {
  const { identity, preferences } = useWorkspace();
  const [currentPage, setCurrentPage] = useState(1);
  const limit = preferences.rowsPerPage;
  const offset = (currentPage - 1) * limit;

  // 1. Fetch policies, scoped to the active company (Settings > Company directory)
  const policiesQuery = usePolicies();
  const companyId = identity.companyId || policiesQuery.data?.items?.[0]?.company_id;

  // 2. Fetch Executive compliance metrics & risk score
  const summaryQuery = useExecutiveSummary(companyId);

  // 3. Fetch paginated compliance audit trail logs
  const auditLogsQuery = useComplianceAuditLogs(companyId, limit, offset);

  const getRiskLevelBadgeClass = (level: string) => {
    switch (level.toLowerCase()) {
      case "low":
        return "bg-green-50 text-green-700 ring-green-600/20 dark:bg-green-500/10 dark:text-green-400 dark:ring-green-500/30";
      case "medium":
        return "bg-amber-50 text-amber-700 ring-amber-600/20 dark:bg-amber-500/10 dark:text-amber-400 dark:ring-amber-500/30";
      case "high":
        return "bg-orange-50 text-orange-700 ring-orange-600/20 dark:bg-orange-500/10 dark:text-orange-400 dark:ring-orange-500/30";
      case "critical":
        return "bg-red-50 text-red-700 ring-red-600/20 dark:bg-red-500/10 dark:text-red-400 dark:ring-red-500/30 animate-pulse";
      default:
        return "bg-neutral-50 text-neutral-600 ring-neutral-500/20 dark:bg-neutral-500/10 dark:text-neutral-400 dark:ring-neutral-500/30";
    }
  };

  const getEventBadgeClass = (type: string) => {
    switch (type.toLowerCase()) {
      case "policy upload":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300";
      case "text extraction":
        return "bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300";
      case "clause segmentation":
        return "bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-300";
      case "obligation extraction":
        return "bg-teal-100 text-teal-800 dark:bg-teal-900/40 dark:text-teal-300";
      case "conflict detection":
        return "bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300";
      case "recommendation generation":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300";
      case "recommendation approval/rejection":
        return "bg-pink-100 text-pink-800 dark:bg-pink-900/40 dark:text-pink-300";
      default:
        return "bg-neutral-100 text-neutral-800 dark:bg-neutral-800 dark:text-neutral-300";
    }
  };

  const isLoading = policiesQuery.isLoading || summaryQuery.isLoading || auditLogsQuery.isLoading;

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-3">
        <Loader2 className="h-10 w-10 animate-spin text-brand-500" />
        <span className="text-sm text-neutral-500">Calculating compliance metrics and generating dashboard...</span>
      </div>
    );
  }

  const summary = summaryQuery.data || {
    total_policies: 0,
    total_clauses: 0,
    total_obligations: 0,
    active_conflicts: 0,
    resolved_conflicts: 0,
    pending_recommendations: 0,
    compliance_score: 100,
    risk_score: 0,
    risk_level: "Low",
    risk_summary: "No compliance summary metrics generated yet."
  };

  const totalPages = Math.ceil((auditLogsQuery.data?.total || 0) / limit);

  // SVG parameters for Compliance Score Dial
  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (summary.compliance_score / 100) * circumference;

  return (
    <div className="flex flex-col h-full gap-8">
      
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-semibold text-foreground dark:text-neutral-100 flex items-center gap-2">
            <Activity className="h-6 w-6 text-brand-500" />
            Dashboard
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-neutral-500">
            How your policies are doing, at a glance.
          </p>
        </div>
        <div className="flex gap-2">
          {companyId && (
            <a
              href={`${API_BASE_URL}/compliance-dashboard/download?company_id=${companyId}`}
              download="compliance_report.pdf"
              className="flex items-center gap-1.5 rounded-md border border-brand-200 bg-brand-50 hover:bg-brand-100 text-brand-700 px-3 py-1.5 text-xs font-semibold dark:border-brand-900/30 dark:bg-brand-500/10 dark:text-brand-300 dark:hover:bg-brand-500/20 transition-colors"
            >
              <FileDown className="h-3.5 w-3.5" />
              Download PDF Report
            </a>
          )}
          <button 
            onClick={() => {
              summaryQuery.refetch();
              auditLogsQuery.refetch();
            }}
            className="flex items-center gap-1.5 rounded-md border border-border bg-surface px-3 py-1.5 text-xs font-semibold text-neutral-700 hover:bg-neutral-50 active:bg-neutral-100 dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-300 dark:hover:bg-neutral-800/80 transition-colors"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </button>
        </div>
      </div>

      {/* Main Grid: Compliance Dial & Risk Card */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Compliance Dial Visual Card */}
        <div className="md:col-span-1 rounded-lg border border-border bg-surface p-6 shadow-sm dark:border-neutral-800 dark:bg-neutral-950 flex flex-col items-center justify-center text-center gap-4">
          <span className="text-sm font-semibold text-neutral-400 uppercase tracking-wider">
            Overall Compliance Score
          </span>
          
          {/* Radial Score Gauge */}
          <div className="relative flex items-center justify-center">
            <svg className="w-36 h-36 transform -rotate-90">
              <circle
                cx="72"
                cy="72"
                r={radius}
                className="stroke-neutral-100 dark:stroke-neutral-800 fill-none"
                strokeWidth="10"
              />
              <circle
                cx="72"
                cy="72"
                r={radius}
                className="stroke-brand-500 transition-all duration-500 fill-none"
                strokeWidth="10"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute flex flex-col items-center">
              <span className="text-3xl font-extrabold text-foreground dark:text-neutral-100">
                {summary.compliance_score}
              </span>
              <span className="text-xs text-neutral-400 font-semibold">/ 100</span>
            </div>
          </div>

          <div className="flex flex-col items-center gap-1.5">
            <span className="text-xs text-neutral-500 font-semibold">RISK LEVEL</span>
            <span className={`inline-flex items-center rounded-full px-3.5 py-1 text-xs font-semibold ring-1 ring-inset ${getRiskLevelBadgeClass(summary.risk_level)}`}>
              {summary.risk_level}
            </span>
          </div>
        </div>

        {/* Risk Summary Description Box */}
        <div className="md:col-span-2 rounded-lg border border-border bg-surface p-6 shadow-sm dark:border-neutral-800 dark:bg-neutral-950 flex flex-col justify-center gap-3">
          <span className="text-sm font-semibold text-foreground dark:text-neutral-100 flex items-center gap-1.5">
            <Shield className="h-4 w-4 text-brand-500" />
            What this means
          </span>
          <p className="text-sm text-neutral-600 dark:text-neutral-300 leading-relaxed">
            {summary.risk_summary}
          </p>
          {summary.compliance_score < 80 && (
            <div className="flex items-center gap-2 text-xs font-medium text-red-600 dark:text-red-400">
              <TrendingDown className="h-4 w-4" />
              Needs attention — review the open conflicts below.
            </div>
          )}
        </div>

      </div>

      {/* Metrics Card Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-6 gap-4">
        {/* Policies */}
        <div className="rounded-lg border border-border bg-surface p-4 shadow-sm dark:border-neutral-800 dark:bg-neutral-950 flex flex-col gap-1">
          <div className="flex justify-between items-center text-neutral-400">
            <span className="text-xs font-bold uppercase tracking-wider">Policies</span>
            <FileText className="h-4 w-4" />
          </div>
          <span className="text-2xl font-bold text-foreground dark:text-neutral-100">{summary.total_policies}</span>
        </div>

        {/* Clauses */}
        <div className="rounded-lg border border-border bg-surface p-4 shadow-sm dark:border-neutral-800 dark:bg-neutral-950 flex flex-col gap-1">
          <div className="flex justify-between items-center text-neutral-400">
            <span className="text-xs font-bold uppercase tracking-wider">Clauses</span>
            <List className="h-4 w-4" />
          </div>
          <span className="text-2xl font-bold text-foreground dark:text-neutral-100">{summary.total_clauses}</span>
        </div>

        {/* Obligations */}
        <div className="rounded-lg border border-border bg-surface p-4 shadow-sm dark:border-neutral-800 dark:bg-neutral-950 flex flex-col gap-1">
          <div className="flex justify-between items-center text-neutral-400">
            <span className="text-xs font-bold uppercase tracking-wider">Obligations</span>
            <Shield className="h-4 w-4" />
          </div>
          <span className="text-2xl font-bold text-foreground dark:text-neutral-100">{summary.total_obligations}</span>
        </div>

        {/* Active Conflicts */}
        <div className="rounded-lg border border-border bg-surface p-4 shadow-sm dark:border-neutral-800 dark:bg-neutral-950 flex flex-col gap-1">
          <div className="flex justify-between items-center text-neutral-400">
            <span className="text-xs font-bold uppercase tracking-wider">Active Conflicts</span>
            <AlertTriangle className="h-4 w-4 text-amber-500" />
          </div>
          <span className="text-2xl font-bold text-foreground dark:text-neutral-100">{summary.active_conflicts}</span>
        </div>

        {/* Resolved Conflicts */}
        <div className="rounded-lg border border-border bg-surface p-4 shadow-sm dark:border-neutral-800 dark:bg-neutral-950 flex flex-col gap-1">
          <div className="flex justify-between items-center text-neutral-400">
            <span className="text-xs font-bold uppercase tracking-wider">Resolved</span>
            <CheckCircle2 className="h-4 w-4 text-green-500" />
          </div>
          <span className="text-2xl font-bold text-foreground dark:text-neutral-100">{summary.resolved_conflicts}</span>
        </div>

        {/* Pending recommendations */}
        <div className="rounded-lg border border-border bg-surface p-4 shadow-sm dark:border-neutral-800 dark:bg-neutral-950 flex flex-col gap-1">
          <div className="flex justify-between items-center text-neutral-400">
            <span className="text-xs font-bold uppercase tracking-wider">Pending Recs</span>
            <Sparkles className="h-4 w-4 text-brand-500" />
          </div>
          <span className="text-2xl font-bold text-foreground dark:text-neutral-100">{summary.pending_recommendations}</span>
        </div>
      </div>

      {/* Immutable Audit Trail List Section */}
      <div className="rounded-lg border border-border bg-surface shadow-sm dark:border-neutral-800 dark:bg-neutral-950 p-6 flex flex-col gap-4">
        <div>
          <h3 className="text-base font-semibold text-foreground dark:text-neutral-100">
            Recent activity
          </h3>
          <p className="mt-1 text-xs text-neutral-500">
            A running record of what's happened to your policies — permanent, so nothing here can be edited or removed.
          </p>
        </div>

        {/* Audit Table */}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-border dark:divide-neutral-800 text-sm">
            <thead>
              <tr className="text-left text-xs font-semibold text-neutral-400 uppercase tracking-wider">
                <th className="pb-3 pr-4">Event</th>
                <th className="pb-3 px-4">Who</th>
                <th className="pb-3 px-4">When</th>
                <th className="pb-3 pl-4">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border dark:divide-neutral-800 text-neutral-700 dark:text-neutral-300">
              {auditLogsQuery.data?.items.map((log) => (
                <tr key={log.id} className="hover:bg-neutral-50/50 dark:hover:bg-neutral-900/30 transition-colors">
                  <td className="py-3 pr-4">
                    <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ${getEventBadgeClass(log.event_type)}`}>
                      {log.event_type}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-xs font-medium">{log.user_identifier}</td>
                  <td className="py-3 px-4 text-xs text-neutral-500" title={new Date(log.occurred_at).toLocaleString()}>
                    {formatRelativeTime(log.occurred_at)}
                  </td>
                  <td className="py-3 pl-4 font-medium text-neutral-900 dark:text-neutral-200">
                    {log.description}
                  </td>
                </tr>
              ))}
              {(!auditLogsQuery.data || auditLogsQuery.data.items.length === 0) && (
                <tr>
                  <td colSpan={4} className="py-8 text-center text-neutral-400 text-xs">
                    Nothing yet — activity shows up here once a policy is uploaded.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination controls */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between border-t border-border pt-4 text-xs text-neutral-500">
            <span>
              Showing Page {currentPage} of {totalPages} ({auditLogsQuery.data?.total || 0} total entries)
            </span>
            <div className="flex gap-2">
              <button
                disabled={currentPage === 1}
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                className="rounded border border-border px-2.5 py-1 hover:bg-neutral-50 disabled:opacity-40"
              >
                Previous
              </button>
              <button
                disabled={currentPage === totalPages}
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                className="rounded border border-border px-2.5 py-1 hover:bg-neutral-50 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

    </div>
  );
}
