# graph/ — Infrastructure Layer: Neo4j Knowledge Graph

Encapsulates all interaction with the Neo4j knowledge graph: driver/session management, Cypher query execution, and graph schema management (nodes/relationships representing policies, clauses, departments, regulations, and their relationships).

Also home to the Graph RAG retrieval logic that feeds relevant graph context into `ai/` for LLM reasoning. Exposed to `services/` only through `domain/interfaces/` contracts.
