# Patterned Ingestion Modules Reference

Hermes Recursive CI includes 6 specialized patterned modules in `src/patterns/` designed to import real-world user and runtime telemetry into the agent's decision loop.

---

## 1. Runtime Telemetry & Crash Ingestion (`telemetry.py`)
- **What it does**: Ingests raw stack traces from Sentry, OpenTelemetry, or runtime exception logs.
- **Why it matters**: Groups crashes by signature and frequency, allowing Hermes to automatically prioritize bug-fix sprint dashes based on real user pain rather than theoretical issues.

## 2. Performance & Traffic Profiler (`profiler.py`)
- **What it does**: Collects latency metrics (p50, p95, p99) and slow database queries.
- **Why it matters**: Generates targeted optimization vectors (e.g. adding cache layers or DB indexes) specifically for routes that exceed latency thresholds.

## 3. Feedback & Issue Tracker Sync (`feedback_sync.py`)
- **What it does**: Bridges GitHub Issues, Jira tickets, and user feedback into structured specifications.
- **Why it matters**: Ensures the agent's feature sprint dashes align directly with capabilities requested by actual users.

## 4. Maintainer Preference Learner (`preferences.py`)
- **What it does**: Records maintainer rejections and rationales, compiling an active rules vector.
- **Why it matters**: Prevents the agent from re-proposing deprecated libraries, antipatterns, or unwanted architecture styles.

## 5. Generic Webhook Gateway (`webhooks.py`)
- **What it does**: Inbound webhook listener with HMAC SHA256 cryptographic verification.
- **Why it matters**: Allows third-party developer platforms (Stripe, GitHub, Sentry) to trigger immediate agent actions on external events.

## 6. Role-Based Access Control (`rbac.py`)
- **What it does**: Multi-tenant authorization matrix (`VIEWER`, `DEVELOPER`, `MAINTAINER`, `OPERATOR`).
- **Why it matters**: Governs who has permission to trigger sprint dashes, snooze proposals, or approve sandboxed merges.
