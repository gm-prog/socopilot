"""Generic JSON webhook connector — extensible for Splunk/Sentinel later."""

from typing import Any

from app.schemas.ingest import WebhookAlertIn


class GenericJsonConnector:
    """Maps arbitrary webhook JSON into validated ingest schema."""

    name = "generic_json"

    def parse(self, payload: dict[str, Any]) -> WebhookAlertIn:
        if "alert" in payload and isinstance(payload["alert"], dict):
            payload = payload["alert"]
        return WebhookAlertIn.model_validate(payload)

    def parse_batch(self, payload: dict[str, Any]) -> list[WebhookAlertIn]:
        if "alerts" in payload and isinstance(payload["alerts"], list):
            return [WebhookAlertIn.model_validate(item) for item in payload["alerts"]]
        return [self.parse(payload)]
