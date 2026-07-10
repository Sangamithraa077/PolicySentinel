# api/dependencies/ — FastAPI Dependency Providers

Reusable `Depends(...)` providers shared across routers, such as:
- Current authenticated user resolution (JWT decode + lookup)
- Database session provider
- Neo4j driver/session provider
- Pagination / query-param parsing helpers

Centralizing these keeps endpoint signatures declarative and testable (dependencies can be overridden in tests).
