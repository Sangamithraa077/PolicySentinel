# domain/entities/ — Core Business Entities

Plain Python objects (no framework/ORM dependency) representing core business concepts, e.g. `Policy`, `PolicyClause`, `Conflict`, `RedundancyGroup`, `StalenessFlag`. These are the heart of the **Domain Layer** and must remain independent of FastAPI, SQLAlchemy, Neo4j drivers, or any external library.
