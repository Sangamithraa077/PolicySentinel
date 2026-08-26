import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertTriangle, RotateCcw } from "lucide-react";

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

/**
 * Root-level safety net. Without this, any uncaught render error
 * (a bad API response shape, a null a component didn't expect, ...)
 * unmounts the entire app and leaves a blank white page — no matter how
 * small or recoverable the actual problem was. Catches at the top of the
 * tree only; it's a last resort, not a substitute for handling expected
 * error states (loading/empty/error) in the components themselves.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("Uncaught render error:", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex h-screen flex-col items-center justify-center gap-4 bg-surface-muted px-6 text-center dark:bg-neutral-950">
          <AlertTriangle className="h-10 w-10 text-red-500" />
          <div>
            <h1 className="text-lg font-semibold text-foreground dark:text-neutral-100">
              Something went wrong
            </h1>
            <p className="mt-1 max-w-sm text-sm text-neutral-500">
              This screen hit an unexpected error. Reloading usually fixes it.
            </p>
          </div>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="flex items-center gap-1.5 rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
          >
            <RotateCcw className="h-4 w-4" />
            Reload
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
