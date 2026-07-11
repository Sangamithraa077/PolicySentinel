export function ProgressBar({ percent }: { percent: number }) {
  const clamped = Math.min(100, Math.max(0, percent));
  return (
    <div
      role="progressbar"
      aria-valuenow={clamped}
      aria-valuemin={0}
      aria-valuemax={100}
      className="h-2 w-full overflow-hidden rounded-full bg-surface-muted dark:bg-neutral-800"
    >
      <div
        className="h-full rounded-full bg-brand-500 transition-all duration-150 ease-out"
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}
