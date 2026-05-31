# SOCoPilot

**AI SIEM Alert Triage & False Positive Reducer**

Enterprise-grade SOC platform foundation for ingesting SIEM alerts, enriching with threat intelligence, AI classification, MITRE ATT&CK mapping, and analyst-ready triage reports.

> **Phase 1** — Generic JSON webhook ingest, normalization, deduplication, alert APIs, and queue UI.

## Stack

| Layer | Technology |
|-------|------------|
| API | FastAPI, SQLAlchemy, Alembic, Pydantic |
| Workers | Celery, Redis |
| Database | PostgreSQL 16 |
| LLM | Ollama (`mistral:7b-instruct`, `nomic-embed-text`) |
| Frontend | React, TypeScript, TailwindCSS |
| Observability | Prometheus, Grafana, Flower |

## Quick Start

### Prerequisites

- Docker Desktop (or Docker Engine + Compose v2)
- 8 GB+ RAM recommended (Ollama models are large)
- Ports: 3000, 3001, 5432, 5555, 6379, 8000, 9090, 11434

### 1. Configure environment

```powershell
cd socopilot
copy .env.example .env
```

### 2. Start the stack

```powershell
# PowerShell
.\scripts\dev.ps1 -Build

# Or Make (Git Bash / WSL)
make up
```

### 3. Pull Ollama models (first run, optional but recommended)

```powershell
docker compose -f docker/docker-compose.yml run --rm ollama-init
```

### 4. Verify

```powershell
.\scripts\verify.ps1
```

## Service URLs

| Service | URL |
|---------|-----|
| API Docs | http://localhost:8000/docs |
| API Health | http://localhost:8000/api/v1/health |
| Readiness | http://localhost:8000/api/v1/ready |
| Frontend | http://localhost:3000 |
| Grafana | http://localhost:3001 (admin / socopilot) |
| Flower | http://localhost:5555 |
| Prometheus | http://localhost:9090 |

## API Examples

### Register tenant + admin

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"changeme123","tenant_name":"acme-soc","role":"admin"}'
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"changeme123"}'
```

### Authenticated profile

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <token>"
```

### Ingest alert (Phase 1)

```bash
curl -X POST http://localhost:8000/api/v1/ingest/alerts \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: $(uuidgen)" \
  -d '{
    "title": "Suspicious login",
    "severity": "high",
    "source": "webhook",
    "rule_id": "auth-001",
    "entities": {"src_ip": ["203.0.113.10"]}
  }'
```

### List alerts

```bash
curl http://localhost:8000/api/v1/alerts \
  -H "Authorization: Bearer <token>"
```

## Project Structure

```
socopilot/
├── backend/           # FastAPI application
├── frontend/          # React dashboard
├── docker/            # Compose & Dockerfiles
├── infra/             # Prometheus & Grafana
├── scripts/           # Dev & verify scripts
└── docs/              # Architecture docs
```

## Troubleshooting: frontend "API unreachable — failed to fetch"

**Cause:** Browser opened `http://127.0.0.1:3000` while the app called `http://localhost:8000` directly — CORS blocked the request (no `Access-Control-Allow-Origin` for 127.0.0.1).

**Fix applied:** Frontend now uses **same-origin** `/api/...` requests proxied by nginx to FastAPI. Works for both `localhost` and `127.0.0.1`.

```powershell
.\scripts\rebuild-frontend.ps1
```

Verify proxy:

```powershell
Invoke-RestMethod http://localhost:3000/api/v1/health
Invoke-RestMethod http://127.0.0.1:3000/api/v1/health
```

Hard-refresh the browser: `Ctrl+Shift+R`.

## Troubleshooting: ingest returns 404

If `POST /api/v1/ingest/alerts` returns `{"detail":"Not Found"}`, the API container is running an **old image** (Phase 0 code only).

```powershell
.\scripts\rebuild-backend.ps1
```

Verify routes inside the container:

```powershell
docker compose -f docker/docker-compose.yml exec api ls /app/app/api/v1
docker compose -f docker/docker-compose.yml exec api python -c "from app.main import app; print([r.path for r in app.routes if 'ingest' in r.path])"
```

Expected: `['/api/v1/ingest/alerts']`

After backend code changes, always rebuild: `.\scripts\dev.ps1 -Build`

## Development

```powershell
# Logs
docker compose -f docker/docker-compose.yml logs -f api

# Run migrations manually
docker compose -f docker/docker-compose.yml exec api alembic upgrade head

# Stop
docker compose -f docker/docker-compose.yml down
```

## Phase Roadmap

| Phase | Scope |
|-------|-------|
| **0** ✅ | Scaffold, auth skeleton, health, Celery, Ollama connectivity |
| **1** ✅ | Generic JSON webhook ingest, normalization, dedup, alert APIs, queue UI |
| **2** ✅ | IOC extraction, TI enrichment, OpenSearch, embeddings stub, workflow, DLQ, replay |
| 3 | AI Triage Agent + Qdrant |
| 4 | MITRE mapping + correlation |
| 5 | Reports + full UI |
| 6 | Analyst feedback loop |

## License

Proprietary — internal use.
