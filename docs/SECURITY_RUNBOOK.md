# Secret Rotation Runbook — SOCoPilot

Operational procedures for rotating every secret this repository has ever
exposed, plus the history-purge status. **Read this fully before rotating in
production.** No secret values belong in this file or in chat — generate them
at the target machine.

---

## 1. Rotate `SECRET_KEY` (JWT signing key)

**Why:** pre-2026-06-08 git history contains a real access token
(`frontend/public/token.txt`, since purged from `main` — see §4) and two
hardcoded seed passwords. Any deployment that used a `SECRET_KEY` from before
that date must rotate so old artifacts are provably useless.

**Generate (on the target host, never in chat/tickets):**

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Apply:**

1. Set `SECRET_KEY=<new value>` in the deployment `.env` (docker compose reads
   `docker/.env` for the api/worker `env_file`; keep it out of git).
2. Restart API **and** all Celery workers (they also call
   `create_access_token`):

   ```bash
   docker compose -f docker/docker-compose.yml up -d --force-recreate api worker-ingest worker-processing worker-enrichment celery-beat
   ```

**Effect:** every outstanding access token and refresh cookie is immediately
invalid (signature check fails). All users must log in again. No data loss.

**Verify (shows where the key came from, never the value):**

```bash
docker compose -f docker/docker-compose.yml exec api python -c \
  "from app.core.config import get_settings; print(get_settings().secret_key_source)"
# expect: environment   (or env_file)
```

Also confirm production can never run on the dev default: the settings layer
rejects `insecure-dev-only-secret-key-change-me-0001` and any known placeholder
whenever `APP_ENV` is not `development`/`test` (startup fails fast with a
remediation message).

---

## 2. Rotate the seeded admin passwords

The historical pairs for `admin@test.com` / `admin@example.com` (values visible
in old commits) must be treated as burned on any real deployment.

**Option A — re-seed a fresh database** (passwords via env, random fallback):

```bash
export SEED_ADMIN_PASSWORD='<new value>'      # admin@test.com
export SEED_ADMIN2_PASSWORD='<new value>'     # admin@example.com
python backend/scripts/seed_admin.py
```

`scripts/dev.ps1` now generates a random `SECRET_KEY` automatically when it
bootstraps `.env`; supply seed passwords explicitly per environment.

**Option B — rotate an existing user in place** (generates the bcrypt hash
without echoing the password into shell history):

```bash
docker compose -f docker/docker-compose.yml exec api python - <<'PY'
from app.core.security import get_password_hash
from getpass import getpass
email = input("email: ")
new = getpass("new password: ")
print("UPDATE users SET hashed_password =",
      repr(get_password_hash(new)), "WHERE email =", repr(email), ";")
PY
# then run the printed UPDATE against Postgres, e.g.:
# docker compose -f docker/docker-compose.yml exec postgres psql -U socopilot -d socopilot
```

**Verify:** old password is rejected (`POST /api/v1/auth/login` → 401), new one
succeeds.

---

## 3. Threat-intel / third-party keys

`ABUSEIPDB_API_KEY`, `VIRUSTOTAL_API_KEY`, `GREYNOISE_API_KEY`,
`SHODAN_API_KEY` were **never committed** (env-only, empty in `.env.example`).
No rotation required for leak reasons; rotate per your normal provider
practice if usage patterns look wrong.

---

## 4. Git-history purge status (2026-09-22)

| Location | Status |
|---|---|
| `main` (default branch) | ✅ **purged** — `frontend/public/token.txt` removed from all commits via `git filter-repo`; verified: zero trees contain the path |
| `arena/01a0c9d5-socopilot` (PR head) | ✅ purged (force-pushed rewrite; final tree byte-identical) |
| `master` branch | ⚠️ **still contains history with the token** — delete or rewrite `master` after the fix PR merges (see §6) |
| Cached PR refs `refs/pull/1..4` (GitHub-side) | ⚠️ **not purgeable via API** — requires a GitHub Support request ("please drop cached PR views for gm-prog/socopilot after a history rewrite") |
| Any existing local clones | ⚠️ re-clone after the rewrite: `git fetch --prune && git gc --aggressive --prune=now`, or simply `rm -rf` and clone fresh |

The token itself expired ~2026-06-28 (exp claim) and is invalidated outright
once §1 is performed.

---

## 5. Ongoing hygiene rules

- Never put real secrets in `.env.example`, scripts, or code — env vars only.
- `.env*` is gitignored (except `.env.example`); keep it that way.
- The dev default `SECRET_KEY` exists only so tests/local boot work; production
  boot refuses it. If you see the startup error, generate a real key (§1).
- `soc.ps1` / `scripts/test-phase1.ps1` take credentials via parameters and
  store tokens only in gitignored `.soc_token`. Never re-add a
  `frontend/public/` token file — anything there ships to browsers.

---

## 6. Retiring the `master` branch (after the fix PR merges)

`main` and `master` were unrelated histories carrying parallel copies of the
project; `master` also preserves the pre-purge history. Once the fix PR is
merged into `main`:

1. Confirm nothing is missing: `git diff origin/master..origin/main --stat`
   should show only the *fix* deltas flowing one way (main ⊇ master content).
2. Delete the branch (GitHub UI → Branches, or
   `gh api -X DELETE repos/gm-prog/socopilot/git/refs/heads/master`).
3. Re-clone locally; old clones keep the burned history in their object store.
4. Then file the GitHub Support request from §4 to clear cached PR refs.

Deleting `master` is the step that finally orphans the old token blob on the
remote (beyond GitHub's internal caches, which Support must clear).
