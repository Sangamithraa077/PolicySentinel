"""Central helper for initializing Google GenAI Client with SSL verification fallback and global circuit breaker."""

import logging
import httpx
from google import genai
from google.genai import types
from backend.config.settings import get_settings, Settings

logger = logging.getLogger(__name__)

_circuit_breaker_tripped = False
_circuit_breaker_reason = ""


def is_circuit_broken() -> bool:
    """Returns True if the Gemini API has been circuit-broken due to quota exhaustion or persistent errors."""
    return _circuit_breaker_tripped


def trip_circuit_breaker(reason: str = "Quota exhausted") -> None:
    """Trips the circuit breaker, causing all subsequent AI operations to immediately use local fallbacks."""
    global _circuit_breaker_tripped, _circuit_breaker_reason
    if not _circuit_breaker_tripped:
        _circuit_breaker_tripped = True
        _circuit_breaker_reason = reason
        logger.warning(
            "AI Circuit Breaker TRIPPED: %s. Switching all AI operations to local deterministic engine.",
            reason,
        )


def reset_circuit_breaker() -> None:
    """Resets the circuit breaker state."""
    global _circuit_breaker_tripped, _circuit_breaker_reason
    _circuit_breaker_tripped = False
    _circuit_breaker_reason = ""


def create_gemini_client(settings: Settings | None = None) -> genai.Client | None:
    if is_circuit_broken():
        return None
    settings = settings or get_settings()
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "changeme":
        return None
    try:
        httpx_client = httpx.Client(verify=False)
        return genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options=types.HttpOptions(httpx_client=httpx_client),
        )
    except Exception as exc:
        logger.error("Failed to initialize Google GenAI client: %s", exc)
        return None

