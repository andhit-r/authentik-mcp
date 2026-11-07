"""Test untuk tool baca-saja domain Source dan parameter superuser_full_list."""

from __future__ import annotations

import httpx
import pytest
import respx
from fastmcp import FastMCP

from tests.conftest import API_BASE, call_tool


@respx.mock
async def test_source_list(mcp: FastMCP) -> None:
    route = respx.get(f"{API_BASE}/sources/all/").mock(
        return_value=httpx.Response(200, json={"results": [{"slug": "google"}]})
    )
    data = await call_tool(mcp, "authentik_source_list", {"search": "goo"})
    assert data["results"][0]["slug"] == "google"
    assert "search=goo" in str(route.calls.last.request.url)


@respx.mock
async def test_source_oauth_list(mcp: FastMCP) -> None:
    route = respx.get(f"{API_BASE}/sources/oauth/").mock(
        return_value=httpx.Response(200, json={"results": [{"slug": "google"}]})
    )
    data = await call_tool(mcp, "authentik_source_oauth_list", {"page_size": 5})
    assert data["results"][0]["slug"] == "google"
    assert "page_size=5" in str(route.calls.last.request.url)


@respx.mock
async def test_source_oauth_get_tanpa_secret(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/sources/oauth/google/").mock(
        return_value=httpx.Response(
            200, json={"slug": "google", "consumer_key": "k", "consumer_secret": "rahasia"}
        )
    )
    data = await call_tool(mcp, "authentik_source_oauth_get", {"slug": "google"})
    assert data["slug"] == "google"
    assert "consumer_secret" not in data
    assert "rahasia" not in str(data)


@respx.mock
async def test_source_oauth_get_404(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/sources/oauth/x/").mock(return_value=httpx.Response(404))
    with pytest.raises(Exception) as exc:
        await call_tool(mcp, "authentik_source_oauth_get", {"slug": "x"})
    assert "tidak ditemukan" in str(exc.value)


@respx.mock
async def test_source_connection_list(mcp: FastMCP) -> None:
    route = respx.get(f"{API_BASE}/sources/user_connections/oauth/").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    await call_tool(mcp, "authentik_source_connection_list", {"source_slug": "google", "user": 7})
    url = str(route.calls.last.request.url)
    assert "source__slug=google" in url
    assert "user=7" in url


@respx.mock
async def test_application_list_superuser_full_list(mcp: FastMCP) -> None:
    route = respx.get(f"{API_BASE}/core/applications/").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    await call_tool(mcp, "authentik_application_list", {"superuser_full_list": True})
    assert "superuser_full_list=true" in str(route.calls.last.request.url)
    await call_tool(mcp, "authentik_application_list", {})
    assert "superuser_full_list" not in str(route.calls.last.request.url)
