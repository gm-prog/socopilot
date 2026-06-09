"""YAML-driven detection rules evaluated on normalized events."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from app.services.severity import _is_failed_login

RULES_DIR = Path(__file__).resolve().parent / "rules"


@dataclass(frozen=True)
class DetectionMatch:
    rule_id: str
    title: str
    severity: str


class DetectionEngine:
    def __init__(self, rules_path: Path | None = None) -> None:
        self._rules_path = rules_path or (RULES_DIR / "default.yaml")
        self._rules = self._load_rules()

    def _load_rules(self) -> list[dict[str, Any]]:
        if not self._rules_path.exists():
            return []
        data = yaml.safe_load(self._rules_path.read_text(encoding="utf-8")) or {}
        return list(data.get("rules") or [])

    def reload(self) -> None:
        self._rules = self._load_rules()

    def evaluate(
        self,
        normalized: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ) -> list[DetectionMatch]:
        ctx = context or {}
        failed_login_count = int(ctx.get("failed_login_count", 0))
        matches: list[DetectionMatch] = []
        for rule in self._rules:
            cond = rule.get("conditions") or {}
            if not self._matches(cond, normalized, failed_login_count=failed_login_count):
                continue
            matches.append(
                DetectionMatch(
                    rule_id=str(rule.get("id", "unknown")),
                    title=str(rule.get("title", rule.get("id", "Detection"))),
                    severity=str(rule.get("severity", "medium")),
                )
            )
        return matches

    def _matches(
        self,
        cond: dict[str, Any],
        normalized: dict[str, Any],
        *,
        failed_login_count: int,
    ) -> bool:
        if not cond:
            return False

        if "failed_logins_gt" in cond:
            threshold = int(cond["failed_logins_gt"])
            if failed_login_count <= threshold:
                return False

        contains = cond.get("event_type_contains")
        if contains:
            needle = str(contains).lower()
            event_type = str(normalized.get("event_type", "")).lower()
            payload_text = str(normalized.get("payload", "")).lower()
            if needle not in event_type and needle not in payload_text:
                return False

        if "require_failed_login" in cond and cond["require_failed_login"]:
            if not _is_failed_login(normalized):
                return False

        return True
