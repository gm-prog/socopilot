# Contributing to SOCoPilot

Thank you for helping improve SOCoPilot. This document explains how to get the project running locally, the branch and PR conventions we use, and checks to run before submitting changes.

## Quick start (local)

Prerequisites:
- Node.js 20+ (frontend)
- Python 3.12 (backend)
- Docker & Docker Compose (for local services)

Backend (Python):

```powershell
cd backend
python -m venv .venv
.
.venv\Scripts\Activate.ps1  # PowerShell (Windows)
# or: source .venv/bin/activate (macOS / Linux)
pip install -r requirements.txt
alembic upgrade head
pytest
```

Frontend (Node):

```bash
cd frontend
npm install
npm run dev
```

Bring up the full stack (local dev):

```powershell
cd ..
docker compose -f docker/docker-compose.yml up --build
```

## Branching
- Use descriptive branch names: `feat/<short-desc>`, `fix/<short-desc>`, `docs/<short-desc>`, `refactor/<short-desc>`
- Open Pull Requests against `develop` (or `main` if your change is urgent)

## PR checklist (required before requesting review)
- Frontend: `npm run lint` and `npm run test` pass
- Backend: `ruff check` and `pytest` pass
- TypeScript: `npm run type-check` passes
- All changed code is documented where applicable
- Database migrations added to `backend/alembic/versions/` when DB schema changes
- No secrets in commits (.env files excluded)

## Code style
- Frontend: ESLint + Prettier. Use the repository ESLint config; prefer strict TypeScript types and Zod for runtime validation.
- Backend: `ruff` for linting and `black` for formatting (consistent with `pyproject.toml`).
- Follow conventional commits where possible: `feat:`, `fix:`, `docs:`, `chore:`.

## Testing and CI
- CI runs frontend lint/tests and backend `pytest`. Ensure tests pass locally before opening a PR.

## Reporting issues
- Use the templates in `.github/ISSUE_TEMPLATE/` for bugs and feature requests. Provide reproduction steps and environment details.

If you're unsure about design or implementation choices, open a draft PR or issue to discuss before implementing large changes.
