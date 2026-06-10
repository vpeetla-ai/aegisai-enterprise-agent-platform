from __future__ import annotations

import os
from pathlib import Path
from typing import Union

from .control_plane_store import SQLiteControlPlaneStore

ControlPlaneStore = Union[SQLiteControlPlaneStore, "PostgresControlPlaneStore"]


def build_control_plane_store() -> ControlPlaneStore:
    """Select persistence backend: sqlite (dev/demo) or postgres (production)."""
    backend = os.getenv("AEGISAI_DB_BACKEND", "sqlite").lower()
    if backend == "postgres":
        database_url = os.getenv("AEGISAI_DATABASE_URL", "").strip()
        if not database_url:
            raise ValueError(
                "AEGISAI_DATABASE_URL is required when AEGISAI_DB_BACKEND=postgres"
            )
        from .postgres_control_plane_store import PostgresControlPlaneStore

        return PostgresControlPlaneStore(database_url)
    db_path = os.getenv("AEGISAI_CONTROL_PLANE_DB_PATH", ":memory:")
    return SQLiteControlPlaneStore(Path(db_path) if db_path != ":memory:" else ":memory:")
