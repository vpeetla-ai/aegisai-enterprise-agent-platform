from __future__ import annotations

import os


def require_execution_token() -> bool:
    return os.getenv("AEGISAI_REQUIRE_EXECUTION_TOKEN", "false").lower() == "true"


def pilot_mode() -> bool:
    return os.getenv("AEGISAI_PILOT_MODE", "false").lower() == "true"


def production_strict() -> bool:
    return os.getenv("PRODUCTION_STRICT", "false").lower() in {"1", "true", "yes", "on"}


def pilot_posture() -> dict[str, object]:
    """Fail-closed profile summary for /health and Architecture UI."""
    enforce_auth = os.getenv("AEGISAI_ENFORCE_AUTH", "false").lower() == "true"
    db_backend = os.getenv("AEGISAI_DB_BACKEND", "sqlite").lower()
    checks = {
        "pilot_mode": pilot_mode(),
        "enforce_auth": enforce_auth,
        "require_execution_token": require_execution_token(),
        "production_strict": production_strict(),
        "postgres_backend": db_backend == "postgres",
    }
    required = ("enforce_auth", "require_execution_token", "production_strict")
    ready = all(checks[key] for key in required) and (
        not checks["pilot_mode"] or checks["postgres_backend"]
    )
    missing = [key for key in required if not checks[key]]
    if checks["pilot_mode"] and not checks["postgres_backend"]:
        missing.append("postgres_backend")
    return {
        "profile": "pilot" if checks["pilot_mode"] else "demo",
        "fail_closed_ready": ready,
        "checks": checks,
        "missing": missing,
        "hint": (
            "Set AEGISAI_PILOT_MODE=true AEGISAI_ENFORCE_AUTH=true "
            "AEGISAI_REQUIRE_EXECUTION_TOKEN=true PRODUCTION_STRICT=true "
            "AEGISAI_DB_BACKEND=postgres for a fail-closed pilot."
        ),
    }
