FROM python:3.14-slim AS builder

# Force Railway rebuild marker (OAuth Redis state store deploy 2026-07-28)
LABEL salesos.oauth_state_redis="2"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Layer cache: install deps from lock before copying application source (CI-22 lock-faithful)
COPY pyproject.toml poetry.lock ./
RUN pip install --no-cache-dir "poetry==2.4.1" \
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
# Required for alembic RLS revisions (generate_rls_policies) — DEC-120 Slice C
COPY scripts/ scripts/

RUN poetry install --only main --no-interaction


FROM python:3.14-slim AS production

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
COPY --from=builder /app/scripts ./scripts
COPY --from=builder /app/alembic.ini .
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

ENV PYTHONPATH="/app"

RUN mkdir -p /data/jwks && chown -R salesos:salesos /app /data/jwks
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

USER salesos

EXPOSE 8000

ENTRYPOINT ["tini", "--", "/usr/local/bin/docker-entrypoint.sh"]
CMD ["api"]
