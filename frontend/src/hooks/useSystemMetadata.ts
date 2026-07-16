import { useQuery } from "@tanstack/react-query";

import { getApiMetadata } from "@/services/systemService";

export function useSystemMetadata() {
  return useQuery({
    queryKey: ["system-metadata"],
    queryFn: getApiMetadata,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}
