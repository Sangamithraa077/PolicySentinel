# ai/ & services/ai/ — AI Layer: Google Gemini AI & Resilient Circuit Breaker

Wraps all interaction with Google Gemini (`google-genai` SDK, model `gemini-2.5-flash`) for obligation extraction, regulatory framework mapping, conflict explanations, and redline drafting with Pydantic JSON schemas.

Includes a global **AI Circuit Breaker** (`gemini_client.py`) that monitors for quota exhaustion (HTTP 429) or connection failures, immediately failing fast and rerouting all AI tasks to deterministic local engines (regex parsing, deontic heuristics, static regulatory knowledge bases) with zero downtime.
