from __future__ import annotations

import os
from pathlib import Path


def require_execution_token() -> bool:
    return os.getenv("AEGISAI_REQUIRE_EXECUTION_TOKEN", "false").lower() == "true"


def pilot_mode() -> bool:
    return os.getenv("AEGISAI_PILOT_MODE", "false").lower() == "true"


def production_strict() -> bool:
    return os.getenv("PRODUCTION_STRICT", "false").lower() in {"1", "true", "yes", "on"}


def policy_engine_preference() -> str:
    return os.getenv("AEGISAI_POLICY_ENGINE", "builtin").strip().lower() or "builtin"


def opa_policy_path() -> Path:
    override = os.getenv("AEGISAI_OPA_POLICY_PATH", "").strip()
    if override:
        return Path(override)
    # interfaces/http → … → repo root is parents[6]
    default = Path(__file__).resolve().parents[6] / "platform" / "policy" / "aegisai.rego"
    if default.is_file():
        return default
    file_path = Path(__file__).resolve()
    for ancestor in file_path.parents:
        candidate = ancestor / "platform" / "policy" / "aegisai.rego"
        if candidate.is_file():
            return candidate
    return default


def policy_plane_status() -> dict[str, object]:
    """Honest OPA/builtin posture for /health and Strict fail-closed demos."""
    from aegisai.application.guardrails.opa_policy import OpaPolicyEngine

    preference = policy_engine_preference()
    opa_binary = OpaPolicyEngine.available()
    policy_file = opa_policy_path()
    policy_file_ok = policy_file.is_file()
    opa_ready = opa_binary and policy_file_ok
    strict = production_strict()
    if preference == "opa" or strict:
        mode = "opa" if opa_ready else "unavailable"
    else:
        mode = "builtin"
    return {
        "mode": mode,
        "preference": preference,
        "opa_binary_available": opa_binary,
        "policy_pack_path": str(policy_file),
        "policy_pack_present": policy_file_ok,
        "fail_closed_for_irreversible": strict,
        "reason": (
            "opa_ready"
            if opa_ready
            else (
                "policy_unavailable"
                if preference == "opa" or strict
                else "demo_builtin"
            )
        ),
    }


def pilot_posture() -> dict[str, object]:
    """Fail-closed profile summary for /health and Architecture UI."""
    enforce_auth = os.getenv("AEGISAI_ENFORCE_AUTH", "false").lower() == "true"
    db_backend = os.getenv("AEGISAI_DB_BACKEND", "sqlite").lower()
    plane = policy_plane_status()
    checks = {
        "pilot_mode": pilot_mode(),
        "enforce_auth": enforce_auth,
        "require_execution_token": require_execution_token(),
        "production_strict": production_strict(),
        "postgres_backend": db_backend == "postgres",
        "policy_plane_ready": plane["mode"] == "opa" or not production_strict(),
    }
    required = ("enforce_auth", "require_execution_token", "production_strict")
    ready = all(checks[key] for key in required) and (
        not checks["pilot_mode"] or checks["postgres_backend"]
    )
    if production_strict() and plane["mode"] != "opa":
        ready = False
    missing = [key for key in required if not checks[key]]
    if checks["pilot_mode"] and not checks["postgres_backend"]:
        missing.append("postgres_backend")
    if production_strict() and plane["mode"] != "opa":
        missing.append("policy_plane_opa")
    return {
        "profile": "pilot" if checks["pilot_mode"] else "demo",
        "fail_closed_ready": ready,
        "checks": checks,
        "missing": missing,
        "policy_plane": plane,
        "hint": (
            "Set AEGISAI_PILOT_MODE=true AEGISAI_ENFORCE_AUTH=true "
            "AEGISAI_REQUIRE_EXECUTION_TOKEN=true PRODUCTION_STRICT=true "
            "AEGISAI_POLICY_ENGINE=opa AEGISAI_DB_BACKEND=postgres "
            "and install the OPA CLI for a fail-closed pilot."
        ),
    }
