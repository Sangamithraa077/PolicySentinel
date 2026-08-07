# uploads/ — Local File Storage (fallback/dev implementation only)

`LocalFileStorageRepository` (`repositories/local_file_storage_repository.py`) writes uploaded policy documents here — but it is **not** what the running app uses by default. `api/dependencies/uploads.py` wires `PostgresFileStorageRepository` instead, storing file bytes in the `stored_files` Postgres table (see `models/file_blob.py`).

Why: Render's free-tier web services have ephemeral local disk — anything written here is lost on the next deploy/restart. Postgres (Neon) persists across deploys for free, so it's the default `FileStorageInterface` implementation for both local dev and production, keeping the two consistent.

`LocalFileStorageRepository` is kept as an alternative implementation of the same interface (e.g. useful behind a real persistent volume, or for tests that don't want DB round-trips) — it's just not DI-wired anywhere currently.

Contents are gitignored — only this README and `.gitkeep` are tracked.
