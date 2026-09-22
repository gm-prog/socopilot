#!/usr/bin/env python3
"""Rotate operational secrets for SOCOPILOT (docs/SECURITY_RUNBOOK.md §1–§2).

Design rules (enforced here, not just documented):
- Secret values are NEVER displayed, logged, or passed on argv. The only
  artifacts written are the target env file and the bcrypt hash in the DB.
- New SECRET_KEY values are generated locally with secrets.token_hex(32).
- New passwords are read from stdin (getpass with confirmation on a TTY,
  --password-stdin for automation), never argv, never shell history.

Usage (from the repo root, or inside the api container):

  python backend/scripts/rotate_secrets.py rotate-key [--env-file PATH]
  python backend/scripts/rotate_secrets.py rotate-password --email EMAIL
                                                  [--password-stdin]
  python backend/scripts/rotate_secrets.py check-password --email EMAIL
                                                  [--password-stdin]
  python backend/scripts/rotate_secrets.py verify

rotate-key:      generate a fresh 256-bit SECRET_KEY directly into the
                 deployment env file (default: first existing of docker/.env
                 then .env). Restart api + all celery workers afterwards.
rotate-password: in-place bcrypt rotation using the application's own hashing
                 utility (app.core.security.get_password_hash), so the result
                 matches auth behavior exactly.
check-password:  verify a candidate password against the stored hash
                 (prints True/False, never the values).
verify:          show where the running SECRET_KEY comes from and audit the
                 admin accounts (email + hash-format only, no values).

Database access uses the application settings (DATABASE_URL / Postgres env
vars) exactly like the api container does.
"""

from __future__ import annotations

import argparse
import getpass
import os
import re
import secrets
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parents[1]
MIN_PASSWORD_LEN = 12


def _load_app() -> None:
    """Make the app package importable and return nothing."""
    sys.path.insert(0, str(BACKEND_DIR))


def _resolve_env_file(explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit).expanduser()
        if not path.exists():
            raise SystemExit(f"error: env file not found: {path}")
        return path
    for candidate in ("docker/.env", ".env"):
        path = REPO_ROOT / candidate
        if path.exists():
            return path
    raise SystemExit(
        "error: no env file found (looked for docker/.env and .env). "
        "Create one from .env.example or pass --env-file PATH."
    )


def cmd_rotate_key(args: argparse.Namespace) -> int:
    env_file = _resolve_env_file(args.env_file)
    new_key = secrets.token_hex(32)  # 256-bit, generated locally

    content = env_file.read_text(encoding="utf-8")
    if re.search(r"(?m)^SECRET_KEY=.*$", content):
        updated = re.sub(r"(?m)^SECRET_KEY=.*$", f"SECRET_KEY={new_key}", content, count=1)
    else:
        updated = content.rstrip("\n") + f"\n\n# JWT signing key (auto-rotated; value never displayed)\nSECRET_KEY={new_key}\n"

    env_file.write_text(updated, encoding="utf-8")
    try:
        env_file.chmod(0o600)  # owner-only; best effort on non-POSIX filesystems
    except OSError:
        pass

    print(f"SECRET_KEY rotated in {env_file} (256-bit random, value not displayed).")
    print("Next: restart api AND all celery workers so the new key is loaded —")
    print("  docker compose -f docker/docker-compose.yml up -d --force-recreate api worker-ingest worker-processing worker-enrichment celery-beat")
    print("All outstanding tokens and refresh cookies are now invalid (users must log in again).")
    return 0


def _read_new_password(verify_twice: bool) -> str:
    if not sys.stdin.isatty():
        password = sys.stdin.readline().rstrip("\n")
        if not password:
            raise SystemExit("error: no password received on stdin")
        return password
    password = getpass.getpass("new password: ")
    if verify_twice:
        if password != getpass.getpass("confirm password: "):
            raise SystemExit("error: passwords do not match")
    return password


def cmd_rotate_password(args: argparse.Namespace) -> int:
    _load_app()
    from sqlalchemy import select

    from app.core.security import get_password_hash
    from app.db.models.user import User
    from app.db.sync_session import SyncSessionLocal

    password = _read_new_password(verify_twice=not args.password_stdin)
    if len(password) < MIN_PASSWORD_LEN:
        raise SystemExit(f"error: password must be at least {MIN_PASSWORD_LEN} characters")
    hashed = get_password_hash(password)

    with SyncSessionLocal() as session:
        users = session.execute(select(User).where(User.email == args.email)).scalars().all()
        if not users:
            raise SystemExit(f"error: no user found with email {args.email}")
        for user in users:
            user.hashed_password = hashed
        session.commit()

    print(f"Password rotated for {len(users)} user account(s) with email {args.email}.")
    print("Note: existing access tokens stay valid until they expire; run rotate-key to invalidate them immediately.")
    return 0


def cmd_check_password(args: argparse.Namespace) -> int:
    _load_app()
    from sqlalchemy import select

    from app.core.security import verify_password
    from app.db.models.user import User
    from app.db.sync_session import SyncSessionLocal

    candidate = _read_new_password(verify_twice=False)
    with SyncSessionLocal() as session:
        users = session.execute(select(User).where(User.email == args.email)).scalars().all()
        if not users:
            raise SystemExit(f"error: no user found with email {args.email}")
        results = {verify_password(candidate, u.hashed_password) for u in users}
    print(f"password matches stored hash for {args.email}: {True in results}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    _load_app()
    from sqlalchemy import func, select

    from app.core.config import get_settings
    from app.db.models.user import User
    from app.db.sync_session import SyncSessionLocal

    settings = get_settings()
    source = settings.secret_key_source
    print(f"SECRET_KEY source: {source}")
    if source == "unknown":
        print("WARNING: no SECRET_KEY found in environment or env files.")

    with SyncSessionLocal() as session:
        total = session.execute(
            select(func.count()).select_from(User).where(User.role == "admin")
        ).scalar_one()
        rows = session.execute(
            select(User.email, User.hashed_password).where(User.role == "admin")
        ).all()

    print(f"admin accounts: {total}")
    for email, hashed in rows:
        bcrypt_ok = hashed.startswith("$2")
        print(f"  {email}  hash-format-bcrypt: {bcrypt_ok}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_key = sub.add_parser("rotate-key", help="generate a fresh SECRET_KEY into the env file")
    p_key.add_argument("--env-file", help="explicit env file (default: docker/.env then .env)")
    p_key.set_defaults(func=cmd_rotate_key)

    p_pw = sub.add_parser("rotate-password", help="rotate a user's password in place")
    p_pw.add_argument("--email", required=True)
    p_pw.add_argument("--password-stdin", action="store_true", help="read password from first stdin line (automation)")
    p_pw.set_defaults(func=cmd_rotate_password)

    p_chk = sub.add_parser("check-password", help="verify a candidate password against the stored hash")
    p_chk.add_argument("--email", required=True)
    p_chk.add_argument("--password-stdin", action="store_true")
    p_chk.set_defaults(func=cmd_check_password)

    p_ver = sub.add_parser("verify", help="show SECRET_KEY source + admin account audit (no values)")
    p_ver.set_defaults(func=cmd_verify)

    args = parser.parse_args()
    return int(args.func(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
