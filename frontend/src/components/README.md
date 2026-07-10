# components/ — Reusable UI Building Blocks

Presentational and reusable React components with no page-level routing awareness. Organized as:
- `common/` — generic, app-agnostic UI primitives (buttons, modals, tables, form fields)
- `layout/` — structural components (navbar, sidebar, page shell) reused across pages

Feature-specific display components (e.g. a "ConflictCard" or "PolicyUploadDropzone") also live here, grouped by feature if the component count grows.
