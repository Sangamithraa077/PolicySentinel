import { QueryClient } from "@tanstack/react-query";

/**
 * Shared TanStack Query client. Sane defaults only — no query/mutation
 * definitions live here; those belong alongside the feature that owns them
 * (e.g. via hooks/ once real data-fetching is implemented).
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
});

export default queryClient;
