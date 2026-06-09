"""Compatibility package for running backend imports from the repository root.

The authoritative application package lives in ``backend/app``. This shim keeps
root-level commands such as ``python -c "import app"`` and
``uvicorn app.main:app`` resolving to that package without duplicating modules.
"""

from __future__ import annotations

from pathlib import Path

_BACKEND_APP = Path(__file__).resolve().parent.parent / "backend" / "app"

if _BACKEND_APP.exists():
    __path__.append(str(_BACKEND_APP))

__version__ = "0.2.0"
