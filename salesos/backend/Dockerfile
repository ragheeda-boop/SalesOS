FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY app/ app/
COPY domains/ domains/
COPY intelligence/ intelligence/
COPY runtime/ runtime/
COPY sdk/ sdk/
COPY modules/ modules/
COPY benchmark/ benchmark/

RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
