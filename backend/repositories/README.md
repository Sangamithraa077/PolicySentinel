# repositories/ — Infrastructure Layer: Data Access

Concrete implementations of the repository interfaces defined in `domain/interfaces/`. Each repository encapsulates all query/persistence logic for one aggregate (e.g. `PolicyRepository`, `ConflictRepository`), so `services/` never construct SQL/Cypher queries directly.

This isolation is what lets PostgreSQL or Neo4j access patterns change without touching business logic in `services/`.
