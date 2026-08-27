Generic single-database configuration with an async dbapi.

## Ongoing workflow — whenever a model changes

```bash
# 1. Edit the SQLAlchemy model(s) in app/entities/

# 2. Generate a migration — diffs your models against the live DB
uv run alembic revision --autogenerate -m "describe the change"

# 3. Open the generated file in alembic/versions/ and read it.
#    Autogenerate is a best-effort diff, not gospel:
#    - check for missing imports (e.g. postgresql dialect types)
#    - check it isn't dropping something it shouldn't
#    - check nullable / server_default choices

# 4. Apply it
uv run alembic upgrade head
```

- Running `alembic upgrade head` with nothing new to apply is always safe — Alembic checks `alembic_version`, sees you're already at head, and does nothing.
- Local app and containerized app can talk to the **same physical Postgres instance** — just via different hostnames (`localhost:5432` from the host, `postgres:5432` inside the Compose network, per the `postgres` service key). Migrations only need to be run once, from wherever is convenient (typically the host) — they apply to the actual database, not to a specific way of connecting to it.
- If a table already exists in Postgres (e.g. created earlier by `create_all()` before Alembic was wired up) and a migration's `upgrade()` tries to `CREATE TABLE` for it again, that fails with "relation already exists." In that situation, use `alembic stamp head` instead of `upgrade head` for that one migration — it records the revision as applied without re-running its SQL. Every migration after that goes through the normal `upgrade head` path.
