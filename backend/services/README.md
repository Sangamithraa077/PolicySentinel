# services/ — Application Layer: Use Cases

Orchestrates domain logic to fulfill specific use cases (e.g. `AnalyzePolicyUploadUseCase`, `DetectConflictsService`, `GenerateStalenessReportService`). Services coordinate calls across `repositories/`, `graph/`, `ai/`, and `reasoning/` through their `domain/interfaces/` contracts — they are the only layer allowed to combine multiple infrastructure concerns into one business workflow.

`api/` endpoints call into `services/`; `services/` never import from `api/`.
