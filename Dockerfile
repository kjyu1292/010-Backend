# =========================
# BUILD STAGE
# =========================
FROM python:3.12.14-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0

# Install dependencies first
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# Copy source code
COPY . .

# Install project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev


# =========================
# PRODUCTION STAGE
# =========================
FROM python:3.12.14-slim-bookworm AS production

WORKDIR /app

RUN useradd --create-home appuser

COPY --from=builder --chown=appuser:appuser /app /app

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

USER appuser

CMD ["python", "main.py"]
