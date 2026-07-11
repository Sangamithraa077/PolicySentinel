/**
 * Client-side pre-validation mirroring the backend's own rules (see
 * backend/services/validate_policy_document_service.py). This is purely
 * a fast, friendly first pass — the server re-validates everything
 * (extension, real file signature, size-while-streaming) regardless,
 * since a client check can always be bypassed.
 */

export const ALLOWED_EXTENSIONS = [".txt", ".md", ".pdf", ".docx"] as const;

// Matches Settings.MAX_UPLOAD_SIZE_MB's default (backend/config/settings.py).
// Keep in sync if that default ever changes.
export const MAX_FILE_SIZE_MB = 25;
export const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

export function fileExtension(filename: string): string {
  const dotIndex = filename.lastIndexOf(".");
  return dotIndex === -1 ? "" : filename.slice(dotIndex).toLowerCase();
}

export function validateUploadFile(file: File): string | null {
  const extension = fileExtension(file.name);
  if (!ALLOWED_EXTENSIONS.includes(extension as (typeof ALLOWED_EXTENSIONS)[number])) {
    return `"${extension || "(no extension)"}" isn't a supported file type. Allowed: ${ALLOWED_EXTENSIONS.join(", ")}.`;
  }
  if (file.size === 0) {
    return "This file is empty.";
  }
  if (file.size > MAX_FILE_SIZE_BYTES) {
    return `This file is larger than the ${MAX_FILE_SIZE_MB} MB limit.`;
  }
  return null;
}

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function isValidUuid(value: string): boolean {
  return UUID_PATTERN.test(value.trim());
}
