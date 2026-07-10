# uploads/ — Infrastructure: Local File Storage

Runtime storage location for uploaded policy documents (PDF/DOCX/etc.) before/after processing. In production this would be backed by object storage (e.g. S3-compatible storage); this folder serves as the local dev equivalent.

Contents are gitignored — only this README and `.gitkeep` are tracked.
