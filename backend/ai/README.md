# ai/ — Infrastructure Layer: Claude API Integration

Wraps all interaction with the Claude API (prompt construction, response parsing, streaming, retries) behind an interface defined in `domain/interfaces/`. Used for tasks like summarizing policy language, explaining detected conflicts in natural language, and powering Graph RAG retrieval-augmented responses.

Kept isolated so the LLM provider/model could be swapped without touching `services/` business logic.
