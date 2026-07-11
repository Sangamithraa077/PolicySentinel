import { useState, type ChangeEvent, type DragEvent } from "react";
import { FileText, UploadCloud, X } from "lucide-react";

import { formatBytes } from "@/utils/formatBytes";
import { ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB } from "@/utils/validateUploadFile";

interface PolicyDropzoneProps {
  file: File | null;
  onFileSelected: (file: File) => void;
  onClear: () => void;
  disabled?: boolean;
}

/** Drag-and-drop zone that doubles as a file picker — the whole zone is a
 * <label> wrapping a hidden file input, so both interactions share one
 * element and one set of styles. */
export function PolicyDropzone({ file, onFileSelected, onClear, disabled }: PolicyDropzoneProps) {
  const [isDragActive, setIsDragActive] = useState(false);

  function handleDrop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    setIsDragActive(false);
    if (disabled) return;
    const dropped = event.dataTransfer.files[0];
    if (dropped) onFileSelected(dropped);
  }

  function handleDragOver(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    if (!disabled) setIsDragActive(true);
  }

  function handleDragLeave(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    setIsDragActive(false);
  }

  function handleInputChange(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0];
    if (selected) onFileSelected(selected);
    // Reset so picking the same file twice in a row still fires onChange.
    event.target.value = "";
  }

  if (file) {
    return (
      <div className="flex items-center justify-between rounded-lg border border-border bg-surface p-4 dark:border-neutral-800 dark:bg-neutral-900">
        <div className="flex items-center gap-3">
          <FileText className="h-8 w-8 shrink-0 text-brand-600" aria-hidden="true" />
          <div>
            <p className="text-sm font-medium text-foreground dark:text-neutral-100">{file.name}</p>
            <p className="text-xs text-neutral-500">{formatBytes(file.size)}</p>
          </div>
        </div>
        {!disabled && (
          <button
            type="button"
            onClick={onClear}
            aria-label="Remove selected file"
            className="rounded-md p-1.5 text-neutral-400 hover:bg-surface-muted hover:text-neutral-600 dark:hover:bg-neutral-800 dark:hover:text-neutral-200"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    );
  }

  return (
    <label
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      className={`flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed p-10 text-center transition-colors ${
        disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"
      } ${
        isDragActive
          ? "border-brand-500 bg-brand-50 dark:bg-brand-500/10"
          : "border-border bg-surface hover:border-brand-500/60 dark:border-neutral-800 dark:bg-neutral-900"
      }`}
    >
      <UploadCloud className="h-8 w-8 text-neutral-400" aria-hidden="true" />
      <p className="text-sm text-neutral-500">
        <span className="font-medium text-brand-600 dark:text-brand-400">Choose a file</span> or
        drag and drop
      </p>
      <p className="text-xs text-neutral-400">
        {ALLOWED_EXTENSIONS.join(", ")} — up to {MAX_FILE_SIZE_MB} MB
      </p>
      <input
        type="file"
        accept={ALLOWED_EXTENSIONS.join(",")}
        className="sr-only"
        onChange={handleInputChange}
        disabled={disabled}
      />
    </label>
  );
}
