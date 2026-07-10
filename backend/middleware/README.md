# middleware/ — Presentation Layer: Request/Response Middleware

ASGI/FastAPI middleware applied globally to every request, e.g.:
- Request logging / correlation IDs
- CORS handling
- Global error-to-HTTP-response translation
- Rate limiting

Runs at the edge of the Presentation Layer, before requests reach `api/` routers.
