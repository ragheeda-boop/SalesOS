FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY app/ app/
COPY domains/ domains/
COPY intelligence/ intelligence/
COPY runtime/ runtime/
COPY sdk/ sdk/
COPY modules/ modules/

RUN pip install --no-cache-dir .


FROM python:3.12-slim AS production

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
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

RUN chown -R salesos:salesos /app

USER salesos

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
