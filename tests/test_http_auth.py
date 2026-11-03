"""Integrasi in-process: auth Bearer pada ASGI ``http_app()`` (di bawah lifespan)."""

from __future__ import annotations

from starlette.testclient import TestClient

from authentik_mcp.server import create_server
from tests.conftest import make_settings

_KEY = "kunci-rahasia-test"
_INIT = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "pytest", "version": "0"},
    },
}
_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


def _app():
    return create_server(make_settings(mcp_api_key=_KEY)).http_app()


def test_tanpa_header_401() -> None:
    with TestClient(_app()) as c:
        resp = c.post("/mcp", json=_INIT, headers=_HEADERS, follow_redirects=True)
    assert resp.status_code == 401


def test_bearer_salah_401() -> None:
    headers = {**_HEADERS, "Authorization": "Bearer salah"}
    with TestClient(_app()) as c:
        resp = c.post("/mcp", json=_INIT, headers=headers, follow_redirects=True)
    assert resp.status_code == 401


def test_bearer_benar_initialize_200() -> None:
    headers = {**_HEADERS, "Authorization": f"Bearer {_KEY}"}
    with TestClient(_app()) as c:
        resp = c.post("/mcp", json=_INIT, headers=headers, follow_redirects=True)
    assert resp.status_code == 200, resp.text


def test_health_tanpa_header_200() -> None:
    with TestClient(_app()) as c:
        assert c.get("/health").status_code == 200
