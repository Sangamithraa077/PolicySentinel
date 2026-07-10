# domain/interfaces/ — Ports (Abstract Contracts)

Abstract interfaces (ports) that the Domain Layer defines and the Infrastructure Layer implements — e.g. `PolicyRepositoryInterface`, `KnowledgeGraphInterface`, `AIReasoningInterface`. Following the Dependency Inversion Principle, `services/` depend on these interfaces, and concrete implementations (`repositories/`, `graph/`, `ai/`) satisfy them at runtime via dependency injection.

This is what keeps the Domain and Application layers testable and swappable — e.g. Neo4j could be replaced without touching business logic.
