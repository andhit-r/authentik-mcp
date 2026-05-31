"""Fixture dan helper bersama untuk unit test authentik-mcp.

Seluruh test memakai mock HTTP (``respx``) sehingga TIDAK pernah memanggil
instance Authentik sungguhan. Base URL Authentik di-set ke domain contoh tetap
``https://auth.example.com``.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastmcp import Client, FastMCP

from authentik_mcp.client import AuthentikClient
from authentik_mcp.config import Settings
from authentik_mcp.server import create_server

# Base URL Authentik yang dipakai konsisten di seluruh test.
BASE_URL = "https://auth.example.com"
API_BASE = f"{BASE_URL}/api/v3"


def make_settings(**overrides: Any) -> Settings:
    """Bangun objek ``Settings`` untuk test dengan nilai default yang aman.

    Args:
        **overrides: Field yang ingin di-override dari default test.

    Returns:
        Instance ``Settings`` siap pakai (tidak membaca ``.env``).
    """
    defaults: dict[str, Any] = {
        "authentik_url": BASE_URL,
        "authentik_api_token": "test-token",
        # Pastikan tidak terbawa nilai dari file .env lingkungan pengembang.
        "oauth_introspection_url": "",
        "oauth_client_id": "",
        "oauth_client_secret": "",
    }
    defaults.update(overrides)
    return Settings(_env_file=None, **defaults)


@pytest.fixture
def settings() -> Settings:
    """Fixture ``Settings`` standar untuk test."""
    return make_settings()


@pytest.fixture
async def client(settings: Settings) -> AuthentikClient:
    """Fixture ``AuthentikClient`` yang siap dimock dengan respx."""
    c = AuthentikClient(settings)
    try:
        yield c
    finally:
        await c.aclose()


@pytest.fixture
def mcp(settings: Settings) -> FastMCP:
    """Fixture instance FastMCP yang sudah terkonfigurasi penuh untuk test."""
    return create_server(settings)


async def call_tool(mcp_server: FastMCP, name: str, arguments: dict[str, Any] | None = None) -> Any:
    """Panggil sebuah tool MCP melalui transport in-memory dan kembalikan datanya.

    Args:
        mcp_server: Instance FastMCP.
        name: Nama tool yang dipanggil.
        arguments: Argumen tool.

    Returns:
        Data hasil tool (``CallToolResult.data``).

    Raises:
        Exception: Bila tool gagal (mis. ``AuthentikAPIError`` dibungkus ToolError).
    """
    async with Client(mcp_server) as c:
        result = await c.call_tool(name, arguments or {})
        return result.data
