"""WebSocket endpoint for real-time alert updates with JWT validation and multi-tenant scoping."""

from __future__ import annotations

import json
from fastapi import APIRouter, WebSocket, status
from starlette.websockets import WebSocketDisconnect

from app.core.logging import get_logger
from app.core.security import TokenValidationError, validate_access_token
from app.realtime.alerts import AlertsWebSocketManager

router = APIRouter(tags=["websockets"])
logger = get_logger(__name__)


@router.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Real-time alert WebSocket stream for authenticated tenant clients."""
    manager: AlertsWebSocketManager = websocket.app.state.alerts_ws_manager
    
    # Extract token from query params or Authorization header
    token = websocket.query_params.get("token")
    if not token:
        auth_header = websocket.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
        elif auth_header:
            token = auth_header

    await websocket.accept()

    if not token:
        logger.info("alerts_socket_auth_failed", reason="missing_token")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized")
        return

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
