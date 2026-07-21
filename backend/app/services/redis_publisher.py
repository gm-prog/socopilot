"""Redis Pub/Sub publisher for real-time alert updates."""

import json
from typing import Any
from uuid import UUID

import redis
from app.core.logging import get_logger

logger = get_logger(__name__)

REDIS_HOST = "redis"
REDIS_PORT = 6379
REDIS_DB = 0
ALERTS_CHANNEL = "socopilot:alerts"


class RedisPublisher:
    """Redis Pub/Sub publisher for real-time updates."""

    def __init__(
        self,
        host: str = REDIS_HOST,
        port: int = REDIS_PORT,
        db: int = REDIS_DB,
    ):
        self.host = host
        self.port = port
        self.db = db
        self._client: redis.Redis | None = None

    def connect(self) -> "RedisPublisher":
        """Establish connection to Redis."""
        try:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
            )
            self._client.ping()
            logger.info("redis_connected", host=self.host, port=self.port)
        except redis.ConnectionError as exc:
            logger.error("redis_connection_failed", error=str(exc))
            self._client = None
            raise
        return self

    def disconnect(self):
        """Close Redis connection."""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self) -> "RedisPublisher":
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def publish_alert_created(
        self,
        alert_id: UUID,
        tenant_id: UUID,
        title: str,
        severity: str,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """
        Publish alert creation event.

        Args:
            alert_id: UUID of the alert.
            tenant_id: Tenant UUID for isolation.
            title: Alert title.
            severity: Alert severity.
            metadata: Optional additional metadata.

        Returns:
            Number of subscribers that received the message.
        """
        if not self._client:
            logger.warning("redis_not_connected")
            return 0

        payload = {
            "event": "alert_created",
            "alert_id": str(alert_id),
            "tenant_id": str(tenant_id),
            "title": title,
            "severity": severity,
            "metadata": metadata or {},
        }

        try:
            count = self._client.publish(ALERTS_CHANNEL, json.dumps(payload))
            logger.info(
                "alert_published",
                alert_id=str(alert_id),
                subscribers=count,
            )
            return count
        except redis.RedisError as exc:
            logger.error("redis_publish_failed", error=str(exc))
            return 0

    def publish_alert_enriched(
        self,
        alert_id: UUID,
        tenant_id: UUID,
        insights: dict[str, Any],
    ) -> int:
        """
        Publish alert enrichment event with AI-generated insights.

        Args:
            alert_id: UUID of the alert.
            tenant_id: Tenant UUID for isolation.
            insights: Structured insights from LLM.

        Returns:
            Number of subscribers that received the message.
        """
        if not self._client:
            logger.warning("redis_not_connected")
            return 0

        payload = {
            "event": "alert_enriched",
            "alert_id": str(alert_id),
            "tenant_id": str(tenant_id),
            "insights": insights,
        }

        try:
            count = self._client.publish(ALERTS_CHANNEL, json.dumps(payload))
            logger.info(
                "enrichment_published",
                alert_id=str(alert_id),
                subscribers=count,
            )
            return count
        except redis.RedisError as exc:
            logger.error("redis_publish_failed", error=str(exc))
            return 0

    def publish_alert_status(
        self,
        alert_id: UUID,
        tenant_id: UUID,
        status: str,
        lifecycle_state: str,
    ) -> int:
        """
        Publish alert status update.

        Args:
            alert_id: UUID of the alert.
            tenant_id: Tenant UUID for isolation.
            status: Alert status (e.g., 'NORMALIZED', 'ENRICHED').
            lifecycle_state: Lifecycle state (e.g., 'new', 'triaged').

        Returns:
            Number of subscribers that received the message.
        """
        if not self._client:
            logger.warning("redis_not_connected")
            return 0

        payload = {
            "event": "alert_status_updated",
            "alert_id": str(alert_id),
            "tenant_id": str(tenant_id),
            "status": status,
            "lifecycle_state": lifecycle_state,
        }

        try:
            count = self._client.publish(ALERTS_CHANNEL, json.dumps(payload))
            logger.info(
                "status_published",
                alert_id=str(alert_id),
                status=status,
            )
            return count
        except redis.RedisError as exc:
            logger.error("redis_publish_failed", error=str(exc))
            return 0
