# Service Operator Guide: Deploying and Running Hermes Recursive CI

This guide is for system administrators and DevOps engineers deploying the Hermes Recursive Agentic CI service.

---

## 1. Prerequisites

- Python 3.7+ (or Docker / Podman)
- Git 2.25+
- Venice AI API Key ([venice.ai](https://venice.ai))
- Telegram Bot Token (from `@BotFather`)

---

## 2. Environment Configuration

Copy `.env.example` to `.env` and configure key secrets:

```bash
cp .env.example .env
```

| Variable | Description | Default |
|---|---|---|
| `VENICE_API_KEY` | Venice AI API authentication token | _(Required)_ |
| `TELEGRAM_BOT_TOKEN` | Bot token from BotFather | _(Required for Telegram)_ |
| `SERVER_PORT` | Port for Web Dashboard & REST API | `18880` |
| `DAILY_TOKEN_BUDGET` | Max daily token burn before circuit breaker | `250000` |
| `DAILY_PR_LIMIT` | Max daily proposals per repository | `5` |
| `DATABASE_PATH` | SQLite database file location | `data/recursive_ci.db` |

---

## 3. Deployment Options

### Option A: Local / Virtual Environment

```bash
# Install core and dev dependencies
pip install -e .[full]

# 1. Audit a target repository
python -m src.cli audit --path ./examples/sample_forked_repo

# 2. Launch the Web Management Dashboard & MCP Server
python -m src.cli server --port 18880

# 3. Launch the Telegram HITL Bot daemon (in a separate terminal)
python -m src.cli bot
```

### Option B: Docker Compose

```bash
docker-compose up -d --build
```

Access the dashboard at `http://localhost:18880`.

---

## 4. Registering a Repository via CLI

Operators can register new repositories into the system immediately:

```bash
python -m src.cli dash --repo sample-forked-repo --path ./examples/sample_forked_repo --batch 3
```

---

## 5. Monitoring & Maintenance

- **Check Health & Resource Consumption:**
  ```bash
  python -m src.cli status
  ```
- **Resetting Tripped Circuit Breakers:**
  If a repository tripped its circuit breaker due to consecutive rejections, an operator can reset its cooldown via the Web UI or by restarting the state cache.
