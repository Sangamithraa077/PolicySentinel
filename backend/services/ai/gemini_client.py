"""Central helper for initializing Google GenAI Client with SSL verification fallback."""

import logging
import httpx
from google import genai
from google.genai import types
from backend.config.settings import get_settings, Settings

logger = logging.getLogger(__name__)


def create_gemini_client(settings: Settings | None = None) -> genai.Client | None:
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
