import pytest
from unittest.mock import AsyncMock
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core.security import create_access_token
from app.realtime.alerts import AlertsWebSocketManager
from app.main import create_app

@pytest.fixture
def client_with_app():
    app = create_app()
    manager = AlertsWebSocketManager()
    manager.redis = AsyncMock()
    app.state.alerts_ws_manager = manager

    with TestClient(app) as client:
        yield client

def test_websocket_unauthorized_missing_token(client_with_app):
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client_with_app.websocket_connect("/api/v1/ws/alerts") as websocket:
            websocket.receive_text()
    assert exc_info.value.code == 1008

def test_websocket_unauthorized_invalid_token(client_with_app):
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client_with_app.websocket_connect("/api/v1/ws/alerts?token=invalid.jwt.token") as websocket:
            websocket.receive_text()
    assert exc_info.value.code == 1008

def test_websocket_authorized_success(client_with_app):
    token = create_access_token("user-1", "00000000-0000-0000-0000-000000000001", "SOC Analyst")

    with client_with_app.websocket_connect(f"/api/v1/ws/alerts?token={token}") as websocket:
        websocket.send_text("ping")
        data = websocket.receive_text()
        assert data == "pong"
