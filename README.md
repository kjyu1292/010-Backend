# 010-Backend

Backend for a mobile game, built ahead of the client (Godot, cross-platform,
iOS-first). Ships and deploys independently of the client — the App Store
review process only ever touches the game binary, never this API.

## Tech stack

- **FastAPI** — async Python web framework
- **PostgreSQL** — primary data store, via SQLAlchemy (async) + asyncpg
- **Redis** — refresh token storage, session state
- **Alembic** — schema migrations
- **uv** — package/dependency management
- **Docker Compose** — local orchestration (app, postgres, redis)
- **k6** — load/stress testing
- **pytest** — unit, integration, and e2e testing

## Architecture

The client and server are fully decoupled — the game app only ever knows one
thing: an HTTPS base URL. Auth uses a JWT access token (short-lived,
stateless, checked on every request with no DB hit) paired with an opaque
refresh token (long-lived, hash-stored in Redis, single-use and rotated on
each refresh). A reused or expired refresh token forces re-login.

Each domain lives in its own package under `app/`, following the same
model/service/router shape:

```
app/
├── auth/          # register, login, refresh, logout, /me
├── players/       # player profile (level, xp, currency, avatar)
├── database/      # engine/session (Postgres), Redis client
└── entities/      # SQLAlchemy models, one file per table
```

New domains (leaderboards, achievements, etc.) follow the same pattern —
their own folder, their own `router`, mounted in `app/app.py`.

## Getting started

**Prerequisites**: Docker, [uv](https://docs.astral.sh/uv/), Python 3.12.

This project uses two env files, since local development and the
containerized app connect to Postgres/Redis differently:
- `.env.local` — `DATABASE_URL`/`REDIS_URL` point at `localhost`
- `.env.docker` — same variables point at Docker service names (`postgres`, `redis`)

**Local dev loop** (app runs on host, Postgres/Redis in Docker):
```bash
uv sync
docker compose up -d postgres redis
uv run main.py
```

**Fully containerized run:**
```bash
docker compose --env-file .env.docker -f docker-compose.yml -f docker-compose.override.yml up -d
```

For database migrations, see [`alembic/README.md`](./alembic/README.md).

Once running, interactive API docs are at `http://localhost:8000/docs`.

## API reference

All routes are versioned under `/v1`. Full request/response schemas are in
the live docs above — this is just the map.

| Method & Path | Purpose | Auth |
|---|---|---|
| `POST /v1/auth/register` | Create account | none |
| `POST /v1/auth/login` | Issue access + refresh token pair | none |
| `POST /v1/auth/refresh` | Rotate refresh token, issue new pair | none (refresh token in body) |
| `POST /v1/auth/logout` | Revoke refresh token | none (refresh token in body) |
| `GET /v1/auth/me` | Current user identity | bearer |
| `GET /v1/players/me` | Player profile (level, xp, currency, avatar) | bearer |
| `PATCH /v1/players/me` | Update avatar | bearer |

## Database

Schema lives in `app/entities/`, one SQLAlchemy model per file. Migrations
live in `alembic/versions/`.

**Important gotcha**: Alembic's autogenerate only sees models that have
actually been imported before `target_metadata` is read. Every entity is
imported centrally in `app/database/__init__.py` (after `Base` is defined)
specifically so new tables are picked up automatically — if a migration
generates an unexpected `DROP TABLE` or misses a new table entirely, check
that the new entity is imported there.

## Testing

Four tiers, mirroring `app/`'s package structure under `tests/`:

```bash
pytest tests/unit -v          # pure functions, no infra
pytest tests/integration -v   # real Postgres+Redis via testcontainers, ephemeral
pytest tests/e2e -v           # full running stack, real HTTP (needs the app up)
k6 run tests/load/preliminary_sweep.js   # RPS, latency percentiles, error rate
```

Unit and integration tests run with zero setup beyond `uv sync` and Docker
being available. E2e and load tests need the real stack running first
(`docker compose up -d` or the local dev loop above).

## Performance

Baseline load testing and the resulting investigation are documented in
[`PERF_LOG_2026-09-03_preliminary-sweep.md`](./PERF_LOG_2026-09-03_preliminary-sweep.md).

Current state: `players/me` (GET/PATCH) and `auth/me` pass their latency
thresholds. `register`/`login` remain above threshold — confirmed to be
bcrypt's CPU cost bound by the host's physical core count, not a code or
database issue (connection pooling and query shape were both tested and
ruled out). Open decision: revise those two thresholds to match this
hardware's real ceiling, or treat further improvement as a horizontal
scaling / dedicated hashing worker problem.

## Project status

1. ✅ Domain model & API contract
2. ✅ Local dev loop (FastAPI + Postgres + Redis)
3. ✅ Auth module — JWT + Redis refresh, rate limiting, logging, tested end-to-end
4. ⬜ Deploy a single instance to a managed platform
5. 🔶 Add plumbing as needed — caching/rate limiting done, message queue not yet needed
6. 🔶 Observability + CI/CD — structured logging done, metrics/tracing/CI pipeline pending
7. ⬜ Scale infra (Kafka, autoscaling, multi-region) — deferred until real traffic exists

## Known limitations

- `register`/`login` latency under load is hardware-bound (see Performance,
  above) — not yet resolved, decision pending.
- No deployed environment yet — everything runs locally via Docker Compose.
- No CI pipeline yet — tests are run manually.
