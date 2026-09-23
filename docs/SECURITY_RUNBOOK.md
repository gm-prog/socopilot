# Secret Rotation Runbook — SOCoPilot

Operational procedures for rotating every secret this repository has ever
exposed, plus the history-purge status. **Read this fully before rotating in
production.** No secret values belong in this file or in chat — generate them
at the target machine.

---

## 1. Rotate `SECRET_KEY` (JWT signing key)

**Why:** pre-2026-06-08 git history contained a real access token
(`frontend/public/token.txt` and `.soc_token`, same blob `b848f4c`, since purged
from all branches via two `filter-repo` runs — see §4) and two hardcoded seed
passwords. Any deployment that used a `SECRET_KEY` from before that date must
rotate so old artifacts are provably useless.

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

## 4. Git-history purge status (2026-09-23 — second purge)

Two purges were required because the first was path-based.

**First purge (2026-09-22):** `git filter-repo --invert-paths --path frontend/public/token.txt`
removed that one path. The same blob `b848f4c67b2635dcfd23b0107072eba560b7aeb4`
survived at `.soc_token` in five commits (`a161257`, `2f23782`, `14e6b4f`,
`4e3b465`, `fa20c00`). Verification by path claimed clean; verification by
blob SHA proved otherwise.

**Second purge (2026-09-23):** `git filter-repo --strip-blobs-with-ids`
with blob IDs:
- `b848f4c67b2635dcfd23b0107072eba560b7aeb4` (`.soc_token` and `frontend/public/token.txt` — same content)
- `37e1584a99e3e91989a4462842ff8b4eee95bb5d` (`frontend/repomix-output.xml`)
- `810cb38876477b74799de8b41970c077689aa86b` (`repomix-output.xml`)
- `bee9402d46abc32296fd645f84d1664bbbcdd137` (`repomix-output.xml`)

All branch refs were rewritten, including `alerts-page-store-migration`.

| Location | Status |
|---|---|
| `main` (default branch) | ✅ **purged (second run)** — blob `b848f4c` removed from all commits via `--strip-blobs-with-ids`; verified by SHA: `git rev-list --objects origin/main \| grep b848f4c` → no output, `main` now 42 commits |
| `alerts-page-store-migration` | ✅ **purged (second run)** — rewritten `e2e488b`, verified clean |
| `arena/01a0ccea-socopilot` | ✅ **purged (second run)** — rewritten `b9da463`, verified clean |
| `master` branch | ✅ deleted in first purge |
| Cached PR refs `refs/pull/1..8` (GitHub-side) | ⚠️ **not purgeable via API** — still serve old history with the blob; requires a GitHub Support request (see `docs/GITHUB_SUPPORT_TICKET.md`). Attempts to `git push --mirror` are rejected with `deny updating a hidden ref` |
| Any existing local clones | ⚠️ re-clone after the second rewrite: `git fetch --prune` will show forced updates on all three branches; `rm -rf` and clone fresh is safest |

The token itself expired ~2026-06-28 (exp claim) and is invalidated outright
once §1 is performed. Severity of remaining `refs/pull/*` exposure is hygiene,
not active incident, because the token is expired and `SECRET_KEY` rotation
(§1) invalidates all JWTs.

**Verification checklist (use blob SHA, not path):**
```bash
git rev-list --objects origin/main | grep b848f4c67b2635dcfd23b0107072eba560b7aeb4  # expect: nothing
git rev-list --objects origin/main | grep -c 'frontend/public/token.txt'          # expect: 0
git rev-list --objects origin/main | grep -c '\.soc_token'                        # expect: 0
git rev-list --objects --all | grep b848f4c67b2635dcfd23b0107072eba560b7aeb4       # expect: hits only in refs/pull/* (needs Support)
```

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
