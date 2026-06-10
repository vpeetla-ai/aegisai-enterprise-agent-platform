# Postgres Production Setup

AegisAI uses **Postgres as the sole system of record** when `AEGISAI_DB_BACKEND=postgres`. There is no SQLite write-through cache in production mode.

## Environment

```bash
export AEGISAI_DB_BACKEND=postgres
export AEGISAI_DATABASE_URL=postgresql://user:password@host:5432/aegisai
```

Install driver:

```bash
UV_CACHE_DIR=.uv-cache uv pip install -e ".[postgres]"
```

## Migrate schema

```bash
psql "$AEGISAI_DATABASE_URL" -f platform/database/postgres-migration.sql
```

The API also applies this migration on startup when using `PostgresControlPlaneStore`.

## Verify

```bash
curl http://localhost:8000/health | jq .persistence
# { "mode": "postgres", "system_of_record": "postgresql" }
```

## Recommended hosting

- **Neon** or **RDS Aurora** for portfolio → pilot
- Enable automated backups and point-in-time recovery before design-partner data
- Use separate databases per environment (dev / staging / prod)
