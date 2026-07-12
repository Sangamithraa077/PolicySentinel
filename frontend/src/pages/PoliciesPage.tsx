import { useNavigate } from "react-router-dom";
import { Loader2, Download, Eye, ShieldCheck, AlertTriangle, FileText, ArrowRight } from "lucide-react";

import { usePolicies } from "@/hooks/usePolicies";
import { policyDownloadUrl } from "@/services/policyService";
import { extractApiErrorMessage } from "@/utils/apiError";

export function PoliciesPage() {
  const navigate = useNavigate();
  const policiesQuery = usePolicies();

  const getStatusBadgeClass = (status: string) => {
    switch (status.toLowerCase()) {
      case "active":
      case "published":
        return "bg-green-50 text-green-700 ring-green-600/10 dark:bg-green-500/10 dark:text-green-400 dark:ring-green-500/20";
      case "draft":
        return "bg-amber-50 text-amber-700 ring-amber-600/10 dark:bg-amber-500/10 dark:text-amber-400 dark:ring-amber-500/20";
      default:
        return "bg-neutral-50 text-neutral-600 ring-neutral-500/10 dark:bg-neutral-500/10 dark:text-neutral-400 dark:ring-neutral-500/20";
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground dark:text-neutral-100">
          Policies Registry
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-neutral-500">
          Browse, download, and review the structural outlines and extracted obligations of your organization's policy documents.
        </p>
      </div>

      <div className="rounded-lg border border-border bg-surface overflow-hidden dark:border-neutral-800 dark:bg-neutral-900">
        {policiesQuery.isPending && (
          <div className="flex flex-col items-center justify-center p-16 gap-2 text-sm text-neutral-500">
            <Loader2 className="h-8 w-8 animate-spin text-brand-600" />
            Loading organization policies...
          </div>
        )}

        {policiesQuery.isError && (
          <div className="p-8 text-center text-sm text-red-600 dark:text-red-400">
            {extractApiErrorMessage(policiesQuery.error, "Failed to load policies.")}
          </div>
        )}

        {policiesQuery.isSuccess && (
          <>
            {policiesQuery.data.items.length === 0 ? (
              <div className="p-16 text-center text-sm text-neutral-500 flex flex-col items-center gap-4">
                <FileText className="h-12 w-12 text-neutral-300 dark:text-neutral-600" />
                <div>
                  <p className="font-semibold text-foreground dark:text-neutral-200">No policies found</p>
                  <p className="text-xs text-neutral-500 mt-1">Get started by uploading your first policy document.</p>
                </div>
                <button
                  onClick={() => navigate("/upload")}
                  className="mt-2 inline-flex items-center gap-2 rounded-md bg-brand-600 px-3.5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-brand-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600"
                >
                  Upload Policy
                  <ArrowRight className="h-3 w-3" />
                </button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-border bg-surface-muted/50 text-xs font-semibold text-neutral-500 dark:border-neutral-800 dark:bg-neutral-950/50 dark:text-neutral-400">
                      <th className="px-6 py-3.5">Policy Document</th>
                      <th className="px-6 py-3.5">Current Version</th>
                      <th className="px-6 py-3.5">Upload Date</th>
                      <th className="px-6 py-3.5">Status</th>
                      <th className="px-6 py-3.5 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border dark:divide-neutral-800 text-sm">
                    {policiesQuery.data.items.map((policy) => {
                      const version = policy.current_version;
                      const uploadDate = version
                        ? new Date(version.uploaded_at).toLocaleDateString(undefined, {
                            year: "numeric",
                            month: "short",
                            day: "numeric",
                          })
                        : "N/A";

                      return (
                        <tr
                          key={policy.id}
                          className="hover:bg-surface-muted/65 transition-colors"
                        >
                          <td className="px-6 py-4">
                            <div className="flex flex-col gap-1">
                              <span className="font-medium text-foreground dark:text-neutral-100">
                                {policy.title}
                              </span>
                              <span className="text-xs text-neutral-400 max-w-sm truncate">
                                {version?.description || "No description provided."}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4 font-mono text-xs text-neutral-600 dark:text-neutral-300">
                            v{version?.version_number ?? 1}
                          </td>
                          <td className="px-6 py-4 text-neutral-500 dark:text-neutral-400">
                            {uploadDate}
                          </td>
                          <td className="px-6 py-4">
                            <span
                              className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset ${getStatusBadgeClass(
                                policy.status
                              )}`}
                            >
                              {policy.status.toUpperCase()}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-right">
                            <div className="flex justify-end gap-2.5">
                              <button
                                onClick={() => navigate(`/clauses?policyId=${policy.id}`)}
                                title="View Segmented Clauses"
                                className="p-1.5 text-neutral-400 hover:text-brand-600 transition-colors"
                              >
                                <Eye className="h-4.5 w-4.5" />
                              </button>
                              <button
                                onClick={() => navigate(`/obligations/${policy.id}`)}
                                title="View Obligations"
                                className="p-1.5 text-neutral-400 hover:text-brand-600 transition-colors"
                              >
                                <ShieldCheck className="h-4.5 w-4.5" />
                              </button>
                              <button
                                onClick={() => navigate(`/conflicts/${policy.id}`)}
                                title="View Conflicts"
                                className="p-1.5 text-neutral-400 hover:text-brand-600 transition-colors"
                              >
                                <AlertTriangle className="h-4.5 w-4.5" />
                              </button>
                              <a
                                href={policyDownloadUrl(policy.id)}
                                download
                                title="Download Document"
                                className="p-1.5 text-neutral-400 hover:text-brand-600 transition-colors"
                              >
                                <Download className="h-4.5 w-4.5" />
                              </a>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default PoliciesPage;
