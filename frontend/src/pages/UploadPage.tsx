import { useState, useEffect, type FormEvent, type ReactNode } from "react";
import { AlertCircle, Loader2, Sparkles, UploadCloud } from "lucide-react";
import { Link } from "react-router-dom";

import { ProgressBar } from "@/components/common/ProgressBar";
import { ToastStack } from "@/components/common/Toast";
import { PolicyDropzone } from "@/components/upload/PolicyDropzone";
import { UploadedPoliciesList } from "@/components/upload/UploadedPoliciesList";
import { useCompanyDirectory } from "@/hooks/useCompanyDirectory";
import { usePolicyUpload } from "@/hooks/usePolicyUpload";
import { useToasts } from "@/hooks/useToasts";
import { useWorkspace } from "@/hooks/useWorkspace";
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
  const { identity, setIdentity, companyLabel } = useWorkspace();
  const directoryQuery = useCompanyDirectory();
  const directory = directoryQuery.data ?? [];

  const [file, setFile] = useState<File | null>(null);
  const [companyId, setCompanyId] = useState(identity.companyId);
  const [uploadedByUserId, setUploadedByUserId] = useState(identity.userId);
  const [policyTitle, setPolicyTitle] = useState("");
  const [versionNumber, setVersionNumber] = useState("1");
  const [description, setDescription] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [addingNewCompany, setAddingNewCompany] = useState(false);

  const upload = usePolicyUpload();
  const { toasts, push: pushToast, dismiss: dismissToast } = useToasts();

  useEffect(() => {
    setCompanyId(identity.companyId);
    setUploadedByUserId(identity.userId);
  }, [identity]);

  // A dropdown of known companies by default; free-text entry only once
  // the user asks for it, or when there's nothing to pick from yet (the
  // very first upload into a brand-new workspace).
  const showNewCompanyInput = addingNewCompany || (directoryQuery.isSuccess && directory.length === 0);

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
          setIdentity({ companyId: companyId.trim(), userId: uploadedByUserId.trim() });
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
        Add a policy file to a company's workspace.
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

          <Field label="Company" error={fieldErrors.companyId}>
            {showNewCompanyInput ? (
              <div className="flex gap-2">
                <input
                  type="text"
                  value={companyId}
                  onChange={(event) => setCompanyId(event.target.value)}
                  disabled={upload.isPending}
                  placeholder="Paste or generate a new company ID"
                  className={inputClasses(Boolean(fieldErrors.companyId))}
                />
                {directory.length > 0 && (
                  <button
                    type="button"
                    onClick={() => setAddingNewCompany(false)}
                    disabled={upload.isPending}
                    className="shrink-0 rounded-md border border-border px-3 text-xs font-semibold text-neutral-600 hover:bg-neutral-50 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
                  >
                    Choose existing
                  </button>
                )}
              </div>
            ) : (
              <div className="flex gap-2">
                <select
                  value={companyId}
                  onChange={(event) => setCompanyId(event.target.value)}
                  disabled={upload.isPending}
                  className={inputClasses(Boolean(fieldErrors.companyId))}
                >
                  <option value="" disabled>
                    Select a company…
                  </option>
                  {directory.map((entry) => (
                    <option key={entry.companyId} value={entry.companyId}>
                      {companyLabel(entry.companyId)} · {entry.policyCount}{" "}
                      {entry.policyCount === 1 ? "policy" : "policies"}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={() => {
                    setAddingNewCompany(true);
                    setCompanyId("");
                  }}
                  disabled={upload.isPending}
                  className="shrink-0 rounded-md border border-border px-3 text-xs font-semibold text-neutral-600 hover:bg-neutral-50 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
                >
                  New company
                </button>
              </div>
            )}
          </Field>

          {showNewCompanyInput && (
            <button
              type="button"
              onClick={() => setCompanyId(crypto.randomUUID())}
              disabled={upload.isPending}
              className="-mt-3 flex w-fit items-center gap-1.5 text-xs font-medium text-brand-600 hover:text-brand-700 dark:text-brand-400"
            >
              <Sparkles className="h-3.5 w-3.5" />
              Generate a new company ID
            </button>
          )}

          <Field label="Uploaded by" error={fieldErrors.uploadedByUserId}>
            <div className="flex gap-2">
              <input
                type="text"
                value={uploadedByUserId}
                onChange={(event) => setUploadedByUserId(event.target.value)}
                disabled={upload.isPending}
                placeholder="Your user ID"
                className={inputClasses(Boolean(fieldErrors.uploadedByUserId))}
              />
              <button
                type="button"
                onClick={() => setUploadedByUserId(crypto.randomUUID())}
                disabled={upload.isPending}
                title="Generate a new user ID"
                className="shrink-0 rounded-md border border-border px-3 text-neutral-500 hover:bg-neutral-50 hover:text-brand-600 dark:border-neutral-700 dark:hover:bg-neutral-800"
              >
                <Sparkles className="h-4 w-4" />
              </button>
            </div>
          </Field>

          <p className="-mt-3 text-xs text-neutral-400">
            First time here? Generate an ID for each, then save them in{" "}
            <Link to="/settings" className="underline hover:text-neutral-600 dark:hover:text-neutral-300">
              Settings
            </Link>{" "}
            so every screen remembers who you are.
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
