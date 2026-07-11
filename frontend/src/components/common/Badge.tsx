import type { ReactNode } from "react";

type BadgeTone = "neutral" | "brand" | "success" | "warning";

const TONE_CLASSES: Record<BadgeTone, string> = {
  neutral: "bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-300",
  brand: "bg-brand-50 text-brand-700 dark:bg-brand-500/15 dark:text-brand-100",
  success: "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300",
  warning: "bg-amber-50 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300",
};

/** Generic status pill — tone is a purely visual signal, callers decide
 * what maps to what (see components/upload/UploadedPoliciesList.tsx). */
export function Badge({ tone = "neutral", children }: { tone?: BadgeTone; children: ReactNode }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${TONE_CLASSES[tone]}`}
    >
      {children}
    </span>
  );
}
