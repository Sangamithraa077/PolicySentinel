"""Shared, reusable FastAPI dependency providers.

Kept separate from config/settings.py so endpoint signatures depend on
this module (overridable via app.dependency_overrides in tests) rather
than importing the settings loader directly.
"""

from config.settings import Settings, get_settings


def get_app_settings() -> Settings:
    return get_settings()
