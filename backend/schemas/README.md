# schemas/ — Application Layer: Data Transfer Objects

Pydantic schemas defining the shape of data crossing the `api/` boundary: request bodies, response payloads, and query parameter models. These decouple the public API contract from both `models/` (DB structure) and `domain/entities/` (business objects), so any one of the three can change without forcing changes in the others.
