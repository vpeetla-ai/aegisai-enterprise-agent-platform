from __future__ import annotations

import os
from pathlib import Path
from typing import Union
from urllib.parse import quote

from .control_plane_store import SQLiteControlPlaneStore

ControlPlaneStore = Union[SQLiteControlPlaneStore, "PostgresControlPlaneStore"]


def normalize_postgres_url(url: str) -> str:
    """Re-encode the password so #, @, and other special chars parse in DATABASE_URL."""
    url = url.strip()
    if not url.startswith(("postgresql://", "postgres://")):
        return url

    scheme_sep = "://"
    scheme_end = url.index(scheme_sep) + len(scheme_sep)
    rest = url[scheme_end:]
    host_sep = rest.rfind("@")
    if host_sep == -1:
        return url

    userinfo = rest[:host_sep]
    location = rest[host_sep + 1 :]
    colon = userinfo.find(":")
    if colon == -1:
        return url

    user = userinfo[:colon]
    password = userinfo[colon + 1 :]
    encoded = quote(password, safe="")
    if encoded == password:
        return url

    scheme = url[: scheme_end - len(scheme_sep)]
    return f"{scheme}{scheme_sep}{user}:{encoded}@{location}"


def _postgres_database_url() -> str:
    """Render/Heroku use DATABASE_URL; local docs also allow AEGISAI_DATABASE_URL."""
    raw = (
        os.getenv("DATABASE_URL", "").strip()
        or os.getenv("AEGISAI_DATABASE_URL", "").strip()
    )
    return normalize_postgres_url(raw) if raw else ""


def build_control_plane_store() -> ControlPlaneStore:
    """Select persistence backend: sqlite (dev/demo) or postgres (production)."""
    backend = os.getenv("AEGISAI_DB_BACKEND", "sqlite").lower()
    if backend == "postgres":
        database_url = _postgres_database_url()
        if not database_url:
            raise ValueError(
                "DATABASE_URL (or AEGISAI_DATABASE_URL) is required when AEGISAI_DB_BACKEND=postgres"
            )
        from .postgres_control_plane_store import PostgresControlPlaneStore

        return PostgresControlPlaneStore(database_url)
    db_path = os.getenv("AEGISAI_CONTROL_PLANE_DB_PATH", ":memory:")
    return SQLiteControlPlaneStore(Path(db_path) if db_path != ":memory:" else ":memory:")
