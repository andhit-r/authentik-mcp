"""Test untuk tool domain System (admin)."""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from fastmcp import FastMCP

from tests.conftest import API_BASE, call_tool


@respx.mock
async def test_system_info(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/admin/system/").mock(
        return_value=httpx.Response(200, json={"runtime": {"python_version": "3.12"}})
    )
    data = await call_tool(mcp, "authentik_system_info", {})
    assert data["runtime"]["python_version"] == "3.12"


@respx.mock
async def test_system_version(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/admin/version/").mock(
        return_value=httpx.Response(
            200,
            json={
                "version_current": "2024.6.0",
                "version_latest": "2024.6.1",
                "outdated": True,
            },
        )
    )
    data = await call_tool(mcp, "authentik_system_version", {})
    assert data["outdated"] is True


@respx.mock
async def test_system_apps(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/admin/apps/").mock(
        return_value=httpx.Response(200, json=[{"name": "authentik.core", "label": "Core"}])
    )
    data = await call_tool(mcp, "authentik_system_apps", {})
    assert data[0]["label"] == "Core"


@respx.mock
async def test_system_settings_get(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/admin/settings/").mock(
        return_value=httpx.Response(200, json={"avatars": "gravatar,initials"})
    )
    data = await call_tool(mcp, "authentik_system_settings_get", {})
    assert data["avatars"] == "gravatar,initials"


@respx.mock
async def test_system_settings_update(mcp: FastMCP) -> None:
    route = respx.patch(f"{API_BASE}/admin/settings/").mock(
        return_value=httpx.Response(200, json={"event_retention": "days=60"})
    )
    data = await call_tool(
        mcp,
        "authentik_system_settings_update",
        {"settings": {"event_retention": "days=60"}},
    )
    assert data["event_retention"] == "days=60"
    body = json.loads(route.calls.last.request.content)
    assert body == {"event_retention": "days=60"}


async def test_system_settings_update_empty(mcp: FastMCP) -> None:
    with pytest.raises(Exception) as exc:
        await call_tool(mcp, "authentik_system_settings_update", {"settings": {}})
    assert "tidak boleh kosong" in str(exc.value)
