import { useState, type FormEvent, type ReactNode } from "react";
import { AlertCircle, Loader2, UploadCloud } from "lucide-react";

import { ProgressBar } from "@/components/common/ProgressBar";
import { ToastStack } from "@/components/common/Toast";
import { PolicyDropzone } from "@/components/upload/PolicyDropzone";
import { UploadedPoliciesList } from "@/components/upload/UploadedPoliciesList";
import { usePolicyUpload } from "@/hooks/usePolicyUpload";
import { useToasts } from "@/hooks/useToasts";
import { extractApiErrorMessage } from "@/utils/apiError";
import { isValidUuid, validateUploadFile } from "@/utils/validateUploadFile";

interface FieldErrors {
  file?: string;
  companyId?: string;
  uploadedByUserId?: string;
  policyTitle?: string;
  versionNumber?: string;
}

export function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [companyId, setCompanyId] = useState("");
  const [uploadedByUserId, setUploadedByUserId] = useState("");
  const [policyTitle, setPolicyTitle] = useState("");
  const [versionNumber, setVersionNumber] = useState("1");
  const [description, setDescription] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  const upload = usePolicyUpload();
  const { toasts, push: pushToast, dismiss: dismissToast } = useToasts();

  function validate(): FieldErrors {
    const errors: FieldErrors = {};

    if (!file) {
      errors.file = "Choose a file to upload.";
    } else {
      const fileError = validateUploadFile(file);
      if (fileError) errors.file = fileError;
    }

    if (!companyId.trim()) {
      errors.companyId = "Company ID is required.";
    } else if (!isValidUuid(companyId)) {
      errors.companyId = "Enter a valid UUID.";
    }

    if (!uploadedByUserId.trim()) {
      errors.uploadedByUserId = "Uploader user ID is required.";
    } else if (!isValidUuid(uploadedByUserId)) {
      errors.uploadedByUserId = "Enter a valid UUID.";
    }

    if (!policyTitle.trim()) {
      errors.policyTitle = "Policy title is required.";
    }

    const parsedVersion = Number(versionNumber);
    if (!Number.isInteger(parsedVersion) || parsedVersion < 1) {
      errors.versionNumber = "Version must be a whole number of 1 or more.";
    }

    return errors;
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();

    const errors = validate();
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0 || !file) return;

    upload.mutate(
      {
        file,
        companyId: companyId.trim(),
        uploadedByUserId: uploadedByUserId.trim(),
        policyTitle: policyTitle.trim(),
        versionNumber: Number(versionNumber),
        description,
      },
      {
        onSuccess: (result) => {
          pushToast("success", `"${result.policy_title}" uploaded successfully.`);
          setFile(null);
          setPolicyTitle("");
          setDescription("");
          setVersionNumber("1");
          setFieldErrors({});
        },
        onError: (error) => {
          pushToast("error", extractApiErrorMessage(error, "Upload failed. Please try again."));
        },
      },
    );
  }

  return (
    <div>
      <ToastStack toasts={toasts} onDismiss={dismissToast} />

      <h1 className="text-2xl font-semibold text-foreground dark:text-neutral-100">
        Upload a policy document
      </h1>
      <p className="mt-2 max-w-2xl text-sm text-neutral-500">
        Upload a policy file to create a new policy record. This stores the document and its
        metadata only — parsing and analysis happen in a later step.
      </p>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-5">
        <form
          onSubmit={handleSubmit}
          noValidate
          className="flex flex-col gap-5 rounded-lg border border-border bg-surface p-5 lg:col-span-2 dark:border-neutral-800 dark:bg-neutral-900"
        >
          <div>
            <PolicyDropzone
              file={file}
              onFileSelected={(selected) => {
                setFile(selected);
                setFieldErrors((prev) => ({ ...prev, file: undefined }));
              }}
              onClear={() => setFile(null)}
              disabled={upload.isPending}
            />
            {fieldErrors.file && <FieldError message={fieldErrors.file} />}
          </div>

          <Field label="Company ID" error={fieldErrors.companyId}>
            <input
              type="text"
              value={companyId}
              onChange={(event) => setCompanyId(event.target.value)}
              disabled={upload.isPending}
              placeholder="e.g. 9616d35e-1830-4999-b5d8-66ea362851f3"
              className={inputClasses(Boolean(fieldErrors.companyId))}
            />
          </Field>

          <Field label="Uploaded by (User ID)" error={fieldErrors.uploadedByUserId}>
            <input
              type="text"
              value={uploadedByUserId}
              onChange={(event) => setUploadedByUserId(event.target.value)}
              disabled={upload.isPending}
              placeholder="e.g. 081a25e6-1b1b-45c8-a626-e173108f52b6"
              className={inputClasses(Boolean(fieldErrors.uploadedByUserId))}
            />
          </Field>

          <p className="-mt-3 text-xs text-neutral-400">
            Company and uploader are plain ID fields for now — they'll come from your session once
            sign-in exists.
          </p>

          <Field label="Policy title" error={fieldErrors.policyTitle}>
            <input
              type="text"
              value={policyTitle}
              onChange={(event) => setPolicyTitle(event.target.value)}
              disabled={upload.isPending}
              placeholder="e.g. Anti-Money Laundering Policy"
              className={inputClasses(Boolean(fieldErrors.policyTitle))}
            />
          </Field>

          <Field label="Version number" error={fieldErrors.versionNumber}>
            <input
              type="number"
              min={1}
              step={1}
              value={versionNumber}
              onChange={(event) => setVersionNumber(event.target.value)}
              disabled={upload.isPending}
              className={inputClasses(Boolean(fieldErrors.versionNumber))}
            />
          </Field>

          <Field label="Description (optional)">
            <textarea
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              disabled={upload.isPending}
              rows={3}
              placeholder="What changed in this version?"
              className={inputClasses(false)}
            />
          </Field>

          {upload.isPending && (
            <div className="space-y-1.5">
              <ProgressBar percent={upload.progress} />
              <p className="text-xs text-neutral-500">Uploading… {upload.progress}%</p>
            </div>
          )}

          <button
            type="submit"
            disabled={upload.isPending}
            className="flex items-center justify-center gap-2 rounded-md bg-brand-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {upload.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <UploadCloud className="h-4 w-4" />
            )}
            {upload.isPending ? "Uploading…" : "Upload policy"}
          </button>
        </form>

        <div className="lg:col-span-3">
          <UploadedPoliciesList />
        </div>
      </div>
    </div>
  );
}

function Field({ label, error, children }: { label: string; error?: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-medium text-foreground dark:text-neutral-100">
        {label}
      </span>
      {children}
      {error && <FieldError message={error} />}
    </label>
  );
}

function FieldError({ message }: { message: string }) {
  return (
    <p className="mt-1.5 flex items-center gap-1.5 text-xs text-red-600 dark:text-red-400">
      <AlertCircle className="h-3.5 w-3.5 shrink-0" />
      {message}
    </p>
  );
}

function inputClasses(hasError: boolean): string {
  const base =
    "w-full rounded-md border bg-surface px-3 py-2 text-sm text-foreground placeholder:text-neutral-400 focus:outline-none focus:ring-2 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-neutral-900 dark:text-neutral-100";
  return hasError
    ? `${base} border-red-400 focus:ring-red-400/40 dark:border-red-500/60`
    : `${base} border-border focus:border-brand-500 focus:ring-brand-500/30 dark:border-neutral-700`;
}

export default UploadPage;
