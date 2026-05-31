"""Severity normalization to canonical levels."""

SEVERITY_ALIASES: dict[str, str] = {
    "info": "informational",
    "information": "informational",
    "informational": "informational",
    "low": "low",
    "medium": "medium",
    "med": "medium",
    "moderate": "medium",
    "high": "high",
    "critical": "critical",
    "crit": "critical",
    "severe": "critical",
    "1": "informational",
    "2": "low",
    "3": "medium",
    "4": "high",
    "5": "critical",
}

CANONICAL_SEVERITIES = frozenset(SEVERITY_ALIASES.values())


def normalize_severity(raw: str | None, default: str = "medium") -> str:
    if not raw:
        return default
    key = raw.strip().lower()
    return SEVERITY_ALIASES.get(key, default if key not in CANONICAL_SEVERITIES else key)
