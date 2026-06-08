"""WebSocket endpoint for realtime alert updates."""

from __future__ import annotations

import json

from fastapi import APIRouter, WebSocket, status
from starlette.websockets import WebSocketDisconnect

from app.core.logging import get_logger
from app.core.security import TokenValidationError, validate_access_token
from app.realtime.alerts import AlertsWebSocketManager

router = APIRouter(tags=["alerts-ws"])
logger = get_logger(__name__)


@router.websocket("/ws/alerts")
async def alerts_socket(websocket: WebSocket) -> None:
    manager: AlertsWebSocketManager = websocket.app.state.alerts_ws_manager
    token = websocket.query_params.get("token") or websocket.headers.get("authorization")
    await websocket.accept()
    try:
        payload = validate_access_token(token)
    except TokenValidationError as exc:
        logger.info("alerts_socket_auth_failed", reason=exc.reason)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized")
        return

    tenant_id = str(payload["tenant_id"])
    await manager.connect(tenant_id, websocket, accepted=True)
    logger.info("alerts_socket_connected", tenant_id=tenant_id)

    try:
        while True:
            raw = await websocket.receive_text()
            if raw == "ping":
                await websocket.send_text("pong")
                continue

            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                logger.debug("alerts_socket_invalid_json", tenant_id=tenant_id)
                continue

            if isinstance(message, dict) and message.get("type") == "PING":
                await websocket.send_json({"type": "PONG"})
    except WebSocketDisconnect:
        logger.info("alerts_socket_disconnected", tenant_id=tenant_id, reason="client_disconnect")
    except Exception as exc:
        logger.warning("alerts_socket_disconnected", error=str(exc), tenant_id=tenant_id)
    finally:
        await manager.disconnect(tenant_id, websocket)
