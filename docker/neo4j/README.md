# docker/neo4j/ — Neo4j Container Config

Uses the official `neo4j:5-community` image directly (no custom Dockerfile needed).

## `conf/`
Custom `neo4j.conf` overrides (e.g. memory heap/page-cache sizing, plugin allowlist for APOC/GDS) can be placed here and mounted into `/conf` by `docker-compose.yml`. Currently empty — default image configuration is used, tuned only via environment variables (`NEO4J_*`) in `docker-compose.yml`.

## Volumes
Neo4j data, logs, import, and plugins directories are persisted via named Docker volumes (see root `docker-compose.yml`), not bind-mounted here, so container upgrades don't require local directory permission management.
