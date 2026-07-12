import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { uploadPolicyDocument, type UploadPolicyDocumentParams } from "@/services/policyService";

type UploadInput = Omit<UploadPolicyDocumentParams, "onProgress">;

/** Uploads a policy document, tracking transfer progress (0-100) and
 * invalidating the policies list on success so it picks up the new entry. */
export function usePolicyUpload() {
  const [progress, setProgress] = useState(0);
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (params: UploadInput) => {
      setProgress(0);
      return uploadPolicyDocument({ ...params, onProgress: setProgress });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["policies"] });
      void queryClient.invalidateQueries({ queryKey: ["compliance-summary"] });
      void queryClient.invalidateQueries({ queryKey: ["compliance-audit-logs"] });
    },
  });

  return { ...mutation, progress };
}
