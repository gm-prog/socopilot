# SOCoPilot

**AI SIEM Alert Triage & False Positive Reducer**

Enterprise-grade SOC platform foundation for ingesting SIEM alerts, enriching with threat intelligence, AI classification, MITRE ATT&CK mapping, and analyst-ready triage reports.

This repository is linked to GitHub:

- `https://github.com/gm-prog/socopilot.git`

---

## Status Summary

- Backend: FastAPI app, authentication, alert ingest, normalization, deduplication, Celery tasks, and health endpoints.
- Frontend: React + TypeScript dashboard with alert listing and investigator note support.
- Docker: `docker/docker-compose.yml` currently defines `postgres`, `redis`, `api`, and `frontend`.
- GitHub CI: `.github/workflows/ci.yml` is present and covers frontend lint/test and backend pytest.

> Current maturity: active development. Functional for local development after dependency setup, but not production-ready or entirely consistent across documentation.

---

## What Works

- Backend API uses FastAPI, SQLAlchemy Async, Alembic migrations, and Celery.
- Frontend uses Vite, React, TypeScript, Zustand, and API client integration.
- GitHub Actions configuration exists for CI.
- Dev scripts simplify stack startup and verification.

## Where the Project Is Fragile

- `docker/docker-compose.yml` is incomplete compared to the docs: it does not declare frontend, Grafana, Prometheus, Flower, or Ollama services.
- Local `pytest` fails unless optional dependencies such as `pgvector` are installed.
- Documentation currently over-promises the running stack versus what the main compose file actually starts.
- The working tree has many modified/untracked files, so the current local branch is not clean.
- Production readiness is not established: no TLS, secrets management, scaling, or hardened deployment docs.

---

## Quick Start

### Prerequisites

- Docker Desktop or Docker Engine + Compose v2
- Node.js 20+ for frontend development
- Python 3.12 for backend dev/test
- 8 GB+ RAM recommended for model support

### 1. Prepare environment

```powershell
cd c:\Users\deysa\OneDrive\Documents\socopilot
copy .env.example .env
```

### 2. Start the stack

```powershell
.\scripts\dev.ps1 -Build
```

### 3. Verify the stack

```powershell
.\scripts\verify.ps1
```

### 4. Run frontend locally

```powershell
cd frontend
npm install
npm run dev
```

---

## Testing

### Backend

```powershell
cd backend
pip install -r requirements.txt
pytest -q
```

### Frontend

```powershell
cd frontend
npm install
npm run lint
npm run test
```

---

## GitHub CI

CI is configured in `.github/workflows/ci.yml` with the following jobs:

- `frontend`: install dependencies, lint, and run tests.
- `backend`: install Python dependencies and run `pytest`.

This is a strong starting point; keep the workflow updated if the package manager or test commands change.

---

## Recommended Improvements

1. Align the main `docker/docker-compose.yml` with README expectations.
2. Add the missing services to Docker compose or update docs to match the actual stack.
3. Add production deployment and secrets guidance.
4. Consolidate backend dependency management between `pyproject.toml` and `requirements.txt`.
5. Clean the git working tree before pushing or tagging releases.
6. Add a simple contributor section and issue template for GitHub.

---

## Project Structure

```
socopilot/
├── backend/           # FastAPI backend, DB models, API routes, Celery tasks
├── frontend/          # React dashboard, API client, UI components
├── docker/            # Compose files and Dockerfiles
├── infra/             # Grafana and Prometheus provisioning
├── scripts/           # Dev and verification scripts
├── docs/              # Architecture documentation
└── .github/           # GitHub Actions CI configuration
```

---

## Current Readiness

- Good for local development once dependencies are installed.
- Not yet a safe production release.
- Needs better documentation around actual service composition and dependency install.
- Requires cleanup of the working tree and verification of the GitHub CI workflow.

---

## License

Proprietary — internal use.
