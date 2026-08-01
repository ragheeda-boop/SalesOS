FROM python:3.12-slim AS builder

# Force Railway rebuild marker (OAuth Redis state store deploy 2026-07-28)
LABEL salesos.oauth_state_redis="2"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Layer cache: install deps from lock before copying application source (CI-22 lock-faithful)
COPY pyproject.toml poetry.lock ./
RUN pip install --no-cache-dir "poetry==1.8.3" \
    && poetry config virtualenvs.create false \
    && poetry install --only main --no-root --no-interaction

COPY alembic.ini .
COPY app/ app/
COPY domains/ domains/
COPY intelligence/ intelligence/
COPY runtime/ runtime/
COPY sdk/ sdk/
COPY modules/ modules/
COPY design_tokens/ design_tokens/

RUN poetry install --only main --no-interaction


FROM python:3.12-slim AS production

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tini \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r salesos && useradd -r -g salesos -d /app -s /sbin/nologin salesos

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app/app ./app
COPY --from=builder /app/domains ./domains
COPY --from=builder /app/intelligence ./intelligence
COPY --from=builder /app/runtime ./runtime
COPY --from=builder /app/sdk ./sdk
COPY --from=builder /app/modules ./modules
COPY --from=builder /app/design_tokens ./design_tokens
COPY --from=builder /app/alembic.ini .

RUN mkdir -p /data/jwks && chown -R salesos:salesos /app /data/jwks

USER salesos

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["tini", "--"]
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
