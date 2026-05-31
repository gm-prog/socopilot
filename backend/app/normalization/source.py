"""Source system normalization."""

SOURCE_ALIASES: dict[str, str] = {
    "generic": "webhook",
    "json": "webhook",
    "webhook": "webhook",
    "http": "webhook",
    "api": "webhook",
    "manual": "manual",
    "splunk": "splunk",
    "sentinel": "sentinel",
    "elastic": "elastic",
    "qradar": "qradar",
}


def normalize_source(raw: str | None, default: str = "webhook") -> str:
    if not raw:
        return default
    key = raw.strip().lower()
    return SOURCE_ALIASES.get(key, key[:100])
