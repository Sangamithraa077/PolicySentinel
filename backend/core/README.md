# core/ — Cross-Cutting Application Core

Framework-agnostic building blocks used across every layer: application startup/bootstrap concerns, shared constants, base exception classes, and cross-cutting infrastructure wiring that doesn't belong to any single feature.

## Typical contents (once implemented)
- Application factory / lifespan wiring
- Global exception handlers
- Shared constants and enums used across layers
- Logging setup (structure only — actual handlers live in `utils/`)

`core/` should never depend on `api/`, `services/`, or `repositories/` — dependencies flow inward toward `core`/`domain`, never outward.
