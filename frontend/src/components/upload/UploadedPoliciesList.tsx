import { Download, FileWarning, Inbox, ListTree, Loader2, RefreshCw } from "lucide-react";
import { Link } from "react-router-dom";

import { Badge } from "@/components/common/Badge";
import { usePolicies } from "@/hooks/usePolicies";
import { policyDownloadUrl } from "@/services/policyService";
import type { Policy, PolicyStatus } from "@/types/policy";
import { extractApiErrorMessage } from "@/utils/apiError";
import { formatBytes } from "@/utils/formatBytes";

const STATUS_TONE: Record<PolicyStatus, "brand" | "neutral" | "warning"> = {
  draft: "neutral",
  active: "brand",
  archived: "neutral",
  superseded: "warning",
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function UploadedPoliciesList() {
  const { data, isPending, isError, error, refetch, isFetching } = usePolicies();

  return (
    <div className="rounded-lg border border-border bg-surface dark:border-neutral-800 dark:bg-neutral-900">
      <div className="flex items-center justify-between border-b border-border px-5 py-4 dark:border-neutral-800">
        <h2 className="text-sm font-semibold text-foreground dark:text-neutral-100">
          Uploaded policies{typeof data?.total === "number" ? ` (${data.total})` : ""}
        </h2>
        <button
          type="button"
          onClick={() => void refetch()}
          disabled={isFetching}
          aria-label="Refresh list"
          className="rounded-md p-1.5 text-neutral-400 hover:bg-surface-muted hover:text-neutral-600 disabled:opacity-50 dark:hover:bg-neutral-800 dark:hover:text-neutral-200"
        >
          <RefreshCw className={`h-4 w-4 ${isFetching ? "animate-spin" : ""}`} />
        </button>
      </div>

      {isPending && (
        <div className="flex items-center gap-2 px-5 py-8 text-sm text-neutral-500">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading policies…
        </div>
      )}

      {isError && (
        <div className="flex items-start gap-2 px-5 py-8 text-sm text-red-600 dark:text-red-400">
          <FileWarning className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{extractApiErrorMessage(error, "Couldn't load policies.")}</span>
        </div>
      )}

      {data && data.items && data.items.length === 0 && (
        <div className="flex flex-col items-center gap-2 px-5 py-10 text-center text-sm text-neutral-500">
          <Inbox className="h-8 w-8 text-neutral-300 dark:text-neutral-700" />
          No policies uploaded yet.
        </div>
      )}

      {data && data.items && data.items.length > 0 && (
        <ul className="divide-y divide-border dark:divide-neutral-800">
          {data.items.map((policy) => (
            <PolicyRow key={policy.id} policy={policy} />
          ))}
        </ul>
      )}
    </div>
  );
}

function PolicyRow({ policy }: { policy: Policy }) {
  const version = policy.current_version;

  return (
    <li className="flex items-center justify-between gap-4 px-5 py-4">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <p className="truncate text-sm font-medium text-foreground dark:text-neutral-100">
            {policy.title}
          </p>
          <Badge tone={STATUS_TONE[policy.status]}>{policy.status}</Badge>
        </div>
        {version ? (
          <p className="mt-1 truncate text-xs text-neutral-500">
            v{version.version_number} · {version.original_filename} ·{" "}
            {formatBytes(version.size_bytes)} · uploaded {formatDate(version.uploaded_at)}
          </p>
        ) : (
          <p className="mt-1 text-xs text-neutral-400">No version on file.</p>
        )}
      </div>

      <div className="flex shrink-0 items-center gap-2">
        <Link
          to={`/clauses/${policy.id}`}
          className="flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-xs font-medium text-neutral-600 transition-colors hover:bg-surface-muted hover:text-foreground dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800 dark:hover:text-neutral-100"
        >
          <ListTree className="h-3.5 w-3.5" />
          View clauses
        </Link>

        {version && (
          <a
            href={policyDownloadUrl(policy.id)}
            className="flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-xs font-medium text-neutral-600 transition-colors hover:bg-surface-muted hover:text-foreground dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800 dark:hover:text-neutral-100"
          >
            <Download className="h-3.5 w-3.5" />
            Download
          </a>
        )}
      </div>
    </li>
  );
}
