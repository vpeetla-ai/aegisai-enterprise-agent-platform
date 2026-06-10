from __future__ import annotations

import os


def require_execution_token() -> bool:
    return os.getenv("AEGISAI_REQUIRE_EXECUTION_TOKEN", "false").lower() == "true"


def pilot_mode() -> bool:
    return os.getenv("AEGISAI_PILOT_MODE", "false").lower() == "true"
