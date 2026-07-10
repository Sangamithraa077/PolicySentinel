# config/ — Configuration Management

Centralized, environment-driven configuration (e.g. Pydantic `Settings` classes) for:
- PostgreSQL connection settings
- Neo4j connection settings
- Claude API credentials/model settings
- JWT secret/expiry settings
- File upload limits/paths
- CORS, logging level, environment name (dev/staging/prod)

Values are sourced from environment variables (see root `.env.example`) — no secrets are ever hardcoded here.
