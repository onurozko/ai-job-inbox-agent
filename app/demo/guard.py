import os

from app.core.config import Settings, get_settings

ALLOWED_DEMO_ENVIRONMENTS = frozenset({"local", "development"})


class DemoScriptsNotAllowedError(RuntimeError):
    pass


def resolve_runtime_environment(settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    return os.environ.get("ENVIRONMENT", settings.app_env)


def ensure_demo_scripts_allowed(settings: Settings | None = None) -> None:
    environment = resolve_runtime_environment(settings)
    if environment not in ALLOWED_DEMO_ENVIRONMENTS:
        raise DemoScriptsNotAllowedError(
            "Demo scripts are only allowed when ENVIRONMENT is 'local' or 'development' "
            f"(current: {environment!r})."
        )
