FROM python:3.11-slim

LABEL maintainer="Autonomous Systems Team"
LABEL description="Recursive Continuous Integration Scaffolding with Venice AI, Hermes Agent, and Telegram"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --upgrade pip && \
    pip install .[full]

COPY . .

RUN mkdir -p /app/data /app/sandboxes

EXPOSE 18880 18881

ENTRYPOINT ["python", "-m", "src.cli"]
CMD ["server", "--host", "0.0.0.0", "--port", "18880"]
