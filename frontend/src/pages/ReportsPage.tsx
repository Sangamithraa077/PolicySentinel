import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Download,
  FileDown,
  FileText,
  Loader2,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { useComplianceAuditLogs, useExecutiveSummary } from "@/hooks/useComplianceDashboard";
import { usePolicies } from "@/hooks/usePolicies";
import { useWorkspace } from "@/hooks/useWorkspace";
import { API_BASE_URL } from "@/services/apiClient";
import { policyDownloadUrl } from "@/services/policyService";

export function ReportsPage() {
  const navigate = useNavigate();
  const { identity } = useWorkspace();
  const policiesQuery = usePolicies();
  const companyId = identity.companyId || policiesQuery.data?.items?.[0]?.company_id;

  const summaryQuery = useExecutiveSummary(companyId);
  const lastActivityQuery = useComplianceAuditLogs(companyId, 1, 0);

  const isLoading = policiesQuery.isLoading || summaryQuery.isLoading;

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-3">
        <Loader2 className="h-10 w-10 animate-spin text-brand-500" />
        <span className="text-sm text-neutral-500">Preparing compliance reports…</span>
      </div>
    );
  }

  if (!companyId) {
    return (
      <div className="flex flex-col gap-6">
        <div>
          <h1 className="text-2xl font-semibold text-foreground dark:text-neutral-100">Reports</h1>
          <p className="mt-2 max-w-2xl text-sm text-neutral-500">
            Generate and download compliance reports across your organization's policies.
          </p>
        </div>
        <div className="rounded-lg border border-border bg-surface p-16 text-center text-sm text-neutral-500 flex flex-col items-center gap-4 dark:border-neutral-800 dark:bg-neutral-950">
          <FileText className="h-12 w-12 text-neutral-300 dark:text-neutral-600" />
          <div>
            <p className="font-semibold text-foreground dark:text-neutral-200">
              No policies uploaded yet
            </p>
            <p className="text-xs text-neutral-500 mt-1">
              Upload at least one policy document to generate a compliance report.
            </p>
          </div>
          <button
            onClick={() => navigate("/upload")}
            className="mt-2 inline-flex items-center gap-2 rounded-md bg-brand-600 px-3.5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-brand-500"
          >
            Upload Policy
            <ArrowRight className="h-3 w-3" />
          </button>
        </div>
      </div>
    );
  }

  const summary = summaryQuery.data;
  const lastEntry = lastActivityQuery.data?.items?.[0];
  const downloadUrl = `${API_BASE_URL}/compliance-dashboard/download?company_id=${companyId}`;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground dark:text-neutral-100">Reports</h1>
        <p className="mt-2 max-w-2xl text-sm text-neutral-500">
          Generate and download compliance reports across your organization's policies.
        </p>
      </div>

      {/* Full compliance report */}
      <div className="rounded-lg border border-border bg-surface p-6 shadow-sm dark:border-neutral-800 dark:bg-neutral-950">
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div className="flex items-start gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-500/10 dark:text-brand-300">
              <FileText className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-foreground dark:text-neutral-100">
                Executive Compliance Report
              </h2>
              <p className="mt-1 max-w-xl text-xs text-neutral-500">
                A generated PDF covering the overall compliance score, active conflicts, AI
                resolution recommendations, and the immutable audit trail — current as of the
                moment you download it.
              </p>
              {lastEntry && (
                <p className="mt-2 text-xs text-neutral-400">
                  Last recorded activity: {lastEntry.description} (
                  {new Date(lastEntry.occurred_at).toLocaleString()})
                </p>
              )}
            </div>
          </div>

          <a
            href={downloadUrl}
            download="compliance_report.pdf"
            className="flex shrink-0 items-center justify-center gap-2 rounded-md bg-brand-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-brand-700"
          >
            <FileDown className="h-4 w-4" />
            Download PDF Report
          </a>
        </div>
      </div>

      {/* Report contents preview */}
      {summary && (
        <div>
          <h3 className="mb-3 text-sm font-semibold text-neutral-500 uppercase tracking-wider">
            What's in this report
          </h3>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard icon={FileText} label="Policies" value={summary.total_policies} />
            <StatCard
              icon={AlertTriangle}
              label="Active Conflicts"
              value={summary.active_conflicts}
              tone="warning"
            />
            <StatCard
              icon={CheckCircle2}
              label="Resolved"
              value={summary.resolved_conflicts}
              tone="success"
            />
            <StatCard
              icon={Sparkles}
              label="Pending Recs"
              value={summary.pending_recommendations}
            />
          </div>
        </div>
      )}

      {/* Per-policy source documents */}
      <div className="rounded-lg border border-border bg-surface overflow-hidden dark:border-neutral-800 dark:bg-neutral-900">
        <div className="border-b border-border px-6 py-4 dark:border-neutral-800">
          <h3 className="text-base font-semibold text-foreground dark:text-neutral-100">
            Policy Documents
          </h3>
          <p className="mt-1 text-xs text-neutral-500">
            Download the original source document for any uploaded policy.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-border bg-surface-muted/50 text-xs font-semibold text-neutral-500 dark:border-neutral-800 dark:bg-neutral-950/50 dark:text-neutral-400">
                <th className="px-6 py-3.5">Policy Document</th>
                <th className="px-6 py-3.5">Version</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5 text-right">Source File</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border dark:divide-neutral-800">
              {policiesQuery.data?.items.map((policy) => (
                <tr key={policy.id} className="hover:bg-surface-muted/65 transition-colors">
                  <td className="px-6 py-4 font-medium text-foreground dark:text-neutral-100">
                    {policy.title}
                  </td>
                  <td className="px-6 py-4 font-mono text-xs text-neutral-600 dark:text-neutral-300">
                    v{policy.current_version?.version_number ?? 1}
                  </td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center gap-1.5 text-xs text-neutral-500">
                      <ShieldCheck className="h-3.5 w-3.5" />
                      {policy.status.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <a
                      href={policyDownloadUrl(policy.id)}
                      download
                      title="Download source document"
                      className="inline-flex items-center gap-1.5 text-xs font-semibold text-brand-600 hover:text-brand-700 dark:text-brand-400"
                    >
                      <Download className="h-3.5 w-3.5" />
                      Download
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  tone = "neutral",
}: {
  icon: typeof FileText;
  label: string;
  value: number;
  tone?: "neutral" | "warning" | "success";
}) {
  const iconClass =
    tone === "warning"
      ? "text-amber-500"
      : tone === "success"
        ? "text-green-500"
        : "text-neutral-400";

  return (
    <div className="rounded-lg border border-border bg-surface p-4 shadow-sm dark:border-neutral-800 dark:bg-neutral-950 flex flex-col gap-1">
      <div className="flex justify-between items-center text-neutral-400">
        <span className="text-xs font-bold uppercase tracking-wider">{label}</span>
        <Icon className={`h-4 w-4 ${iconClass}`} />
      </div>
      <span className="text-2xl font-bold text-foreground dark:text-neutral-100">{value}</span>
    </div>
  );
}

export default ReportsPage;
