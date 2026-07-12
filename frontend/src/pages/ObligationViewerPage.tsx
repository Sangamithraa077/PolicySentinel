import { FileWarning, Loader2 } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import { ObligationViewer } from "@/components/obligations/ObligationViewer";
import { usePolicies } from "@/hooks/usePolicies";
import { extractApiErrorMessage } from "@/utils/apiError";

export function ObligationViewerPage() {
  const { policyId } = useParams<{ policyId?: string }>();
  const navigate = useNavigate();
  const policiesQuery = usePolicies();

  return (
    <div>
      <h1 className="text-2xl font-semibold text-foreground dark:text-neutral-100">
        Obligation viewer
      </h1>
      <p className="mt-2 max-w-2xl text-sm text-neutral-500">
        Browse compliance obligations extracted by AI, filter by category or modality, search key fields, and inspect the source clauses.
      </p>

      <div className="mt-6 max-w-md">
        <label className="block">
          <span className="mb-1.5 block text-sm font-medium text-foreground dark:text-neutral-100">
            Policy
          </span>
          {policiesQuery.isPending && (
            <div className="flex items-center gap-2 text-sm text-neutral-500">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading policies…
            </div>
          )}
          {policiesQuery.isError && (
            <div className="flex items-center gap-2 text-sm text-red-600 dark:text-red-400">
              <FileWarning className="h-4 w-4 shrink-0" />
              {extractApiErrorMessage(policiesQuery.error, "Couldn't load policies.")}
            </div>
          )}
          {policiesQuery.isSuccess && (
            <select
              value={policyId ?? ""}
              onChange={(event) =>
                navigate(event.target.value ? `/obligations/${event.target.value}` : "/obligations")
              }
              className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-100"
            >
              <option value="">Select a policy…</option>
              {policiesQuery.data.items.map((policy) => (
                <option key={policy.id} value={policy.id}>
                  {policy.title}
                </option>
              ))}
            </select>
          )}
        </label>
      </div>

      <div className="mt-6">
        {policyId ? (
          <ObligationViewer key={policyId} policyId={policyId} />
        ) : (
          <p className="rounded-lg border border-dashed border-border p-10 text-center text-sm text-neutral-500 dark:border-neutral-800">
            Select a policy above to view its compliance obligations.
          </p>
        )}
      </div>
    </div>
  );
}

export default ObligationViewerPage;
