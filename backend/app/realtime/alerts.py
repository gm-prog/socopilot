"""Alert realtime delivery via Redis pub/sub and WebSockets."""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from contextlib import suppress
from typing import Any
from uuid import UUID

import redis
import redis.asyncio as aioredis
from fastapi import WebSocket

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.models.normalized_alert import NormalizedAlert
from app.schemas.alerts import AlertSummary

logger = get_logger(__name__)

ALERTS_CHANNEL = "socopilot:alerts"
SEND_TIMEOUT_SECONDS = 5.0

_sync_redis_client: redis.Redis | None = None


# =========================
# SERIALIZATION
# =========================
def serialize_alert_summary(
    alert: NormalizedAlert | AlertSummary | dict[str, Any],
) -> dict[str, Any]:
    return AlertSummary.model_validate(alert).model_dump(mode="json")


# =========================
# SYNC REDIS (PUB)
# =========================
def _reset_sync_redis_client() -> None:
    global _sync_redis_client
    if _sync_redis_client is not None:
        with suppress(Exception):
            _sync_redis_client.close()
    _sync_redis_client = None


def _get_sync_redis_client() -> redis.Redis | None:
    """
    DEV SAFE:
    Returns None if Redis is unavailable instead of crashing system.
    """
    global _sync_redis_client
    settings = get_settings()

    try:
        if _sync_redis_client is None:
            _sync_redis_client = redis.Redis.from_url(
                settings.redis_url,
                decode_responses=True,
            )
        return _sync_redis_client
    except Exception as exc:
        logger.warning("redis_sync_unavailable", error=str(exc))
        return None


# =========================
# PUBLISH ALERT
# =========================
def publish_new_alert(
    *,
    tenant_id: UUID,
    alert: NormalizedAlert | AlertSummary | dict[str, Any],
) -> bool:
    try:
        serialized_alert = serialize_alert_summary(alert)
    except Exception as exc:
        logger.warning(
            "alert_publish_invalid_payload",
            error=str(exc),
            tenant_id=str(tenant_id),
        )
        return False

    payload = {
        "tenant_id": str(tenant_id),
        "type": "NEW_ALERT",
        "data": serialized_alert,
    }

    redis_client = _get_sync_redis_client()

    # 👉 DEV MODE SAFE EXIT
    if redis_client is None:
        logger.warning("alert_publish_skipped_no_redis", tenant_id=str(tenant_id))
        return False

    try:
        subscribers = redis_client.publish(
            ALERTS_CHANNEL,
            json.dumps(payload),
        )
        logger.info(
            "alert_published",
            tenant_id=str(tenant_id),
            alert_id=serialized_alert.get("id"),
            subscribers=subscribers,
        )
        return True

    except Exception as exc:
        logger.warning(
            "alert_publish_failed",
            error=str(exc),
            tenant_id=str(tenant_id),
        )
        _reset_sync_redis_client()
        return False


# =========================
# WEBSOCKET MANAGER
# =========================
class AlertsWebSocketManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, tenant_id: str, websocket: WebSocket, *, accepted: bool = False) -> None:
        if not accepted:
            await websocket.accept()

        async with self._lock:
            self._connections[tenant_id].add(websocket)

    async def disconnect(self, tenant_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            connections = self._connections.get(tenant_id)
            if not connections:
                return

            connections.discard(websocket)

            if not connections:
                self._connections.pop(tenant_id, None)

    async def broadcast(self, tenant_id: str, message: dict[str, Any]) -> None:
        async with self._lock:
            targets = list(self._connections.get(tenant_id, ()))

        stale: list[WebSocket] = []

        for websocket in targets:
            try:
                await asyncio.wait_for(
                    websocket.send_json(message),
                    timeout=SEND_TIMEOUT_SECONDS,
                )
            except Exception as exc:
                logger.debug("ws_send_failed", tenant_id=tenant_id, error=str(exc))
                stale.append(websocket)

        for websocket in stale:
            await self.disconnect(tenant_id, websocket)


# =========================
# EVENT BROKER (FIXED)
# =========================
class AlertsEventBroker:
    def __init__(self) -> None:
        self._redis: aioredis.Redis | None = None
        self._pubsub: aioredis.client.PubSub | None = None
        self._task: asyncio.Task[None] | None = None
        self._enabled: bool = True  # DEV SAFE SWITCH

    async def start(self, manager: AlertsWebSocketManager) -> None:
        if self._task is not None:
            return

        self._task = asyncio.create_task(self._run(manager))
        logger.info("alerts_event_broker_started", channel=ALERTS_CHANNEL)

    async def stop(self) -> None:
        task = self._task
        self._task = None

        if task is not None:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

        await self._reset_connections()

    async def _reset_connections(self) -> None:
        if self._pubsub is not None:
            with suppress(Exception):
                await self._pubsub.unsubscribe(ALERTS_CHANNEL)
                await self._pubsub.close()
            self._pubsub = None

        if self._redis is not None:
            with suppress(Exception):
                await self._redis.close()
            self._redis = None

    async def _ensure_connected(self) -> bool:
        """
        Returns False if Redis is unavailable (safe mode).
        """
        if not self._enabled:
            return False

        settings = get_settings()

        try:
            if self._redis is None:
                self._redis = aioredis.from_url(
                    settings.redis_url,
                    decode_responses=True,
                )

            if self._pubsub is None:
                self._pubsub = self._redis.pubsub()
                await self._pubsub.subscribe(ALERTS_CHANNEL)

                logger.info(
                    "alerts_event_broker_connected",
                    channel=ALERTS_CHANNEL,
                )

            return True

        except Exception as exc:
            logger.warning(
                "redis_broker_disabled",
                error=str(exc),
            )
            await self._reset_connections()
            return False

    async def _run(self, manager: AlertsWebSocketManager) -> None:
        backoff_seconds = 1.0

        while True:
            try:
                ok = await self._ensure_connected()

                # 👉 DEV MODE: if redis not available, just idle
                if not ok or self._pubsub is None:
                    await asyncio.sleep(2.0)
                    continue

                message = await self._pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )

                if message is None:
                    continue

                raw = message.get("data")
                if not isinstance(raw, str):
                    continue

                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError:
                    logger.warning("alerts_event_invalid_json")
                    continue

                tenant_id = payload.pop("tenant_id", None)

                if not isinstance(tenant_id, str):
                    logger.warning("alerts_event_missing_tenant")
                    continue

                await manager.broadcast(tenant_id, payload)
                backoff_seconds = 1.0

            except asyncio.CancelledError:
                raise

            except Exception as exc:
                logger.warning(
                    "alerts_event_broker_reconnect_attempt",
                    error=str(exc),
                )

                await self._reset_connections()
                await asyncio.sleep(backoff_seconds)

                logger.info(
                    "alerts_event_broker_reconnect_wait_complete",
                    backoff_seconds=backoff_seconds,
                )

                backoff_seconds = min(backoff_seconds * 2, 10.0)