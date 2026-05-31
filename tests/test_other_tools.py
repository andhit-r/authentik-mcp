"""Test untuk tool domain Applications, Providers, Tokens, Events, Flows,
Property Mappings, dan Outposts."""

from __future__ import annotations

import httpx
import pytest
import respx
from fastmcp import FastMCP

from tests.conftest import API_BASE, call_tool

UUID = "22222222-2222-2222-2222-222222222222"


# --- Applications ---
@respx.mock
async def test_application_list(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/core/applications/").mock(
        return_value=httpx.Response(200, json={"results": [{"slug": "grafana"}]})
    )
    data = await call_tool(mcp, "authentik_application_list", {})
    assert data["results"][0]["slug"] == "grafana"


@respx.mock
async def test_application_get(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/core/applications/grafana/").mock(
        return_value=httpx.Response(200, json={"slug": "grafana"})
    )
    data = await call_tool(mcp, "authentik_application_get", {"slug": "grafana"})
    assert data["slug"] == "grafana"


# --- Providers ---
@respx.mock
async def test_provider_list(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/providers/all/").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    data = await call_tool(mcp, "authentik_provider_list", {})
    assert data == {"results": []}


@respx.mock
async def test_provider_get_oauth2(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/providers/oauth2/3/").mock(
        return_value=httpx.Response(200, json={"pk": 3, "name": "oauth"})
    )
    data = await call_tool(
        mcp, "authentik_provider_get", {"provider_type": "oauth2", "provider_id": 3}
    )
    assert data["pk"] == 3


async def test_provider_get_invalid_type(mcp: FastMCP) -> None:
    with pytest.raises(Exception) as exc:
        await call_tool(
            mcp,
            "authentik_provider_get",
            {"provider_type": "unknown", "provider_id": 1},
        )
    assert "provider_type tidak valid" in str(exc.value)


# --- Tokens ---
@respx.mock
async def test_token_create(mcp: FastMCP) -> None:
    route = respx.post(f"{API_BASE}/core/tokens/").mock(
        return_value=httpx.Response(201, json={"identifier": "ci-token"})
    )
    data = await call_tool(
        mcp,
        "authentik_token_create",
        {"identifier": "ci-token", "user_id": 1},
    )
    assert data["identifier"] == "ci-token"
    assert "api" in route.calls.last.request.content.decode()


@respx.mock
async def test_token_revoke(mcp: FastMCP) -> None:
    respx.delete(f"{API_BASE}/core/tokens/ci-token/").mock(return_value=httpx.Response(204))
    data = await call_tool(mcp, "authentik_token_revoke", {"identifier": "ci-token"})
    assert data["status"] == "revoked"


# --- Events ---
@respx.mock
async def test_event_filter_by_action(mcp: FastMCP) -> None:
    route = respx.get(f"{API_BASE}/events/events/").mock(
        return_value=httpx.Response(200, json={"results": [{"action": "login_failed"}]})
    )
    data = await call_tool(mcp, "authentik_event_filter_by_action", {"action": "login_failed"})
    assert data["results"][0]["action"] == "login_failed"
    assert "action=login_failed" in str(route.calls.last.request.url)


@respx.mock
async def test_event_filter_by_user(mcp: FastMCP) -> None:
    route = respx.get(f"{API_BASE}/events/events/").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    await call_tool(mcp, "authentik_event_filter_by_user", {"username": "alice"})
    assert "username=alice" in str(route.calls.last.request.url)


# --- Flows ---
@respx.mock
async def test_flow_execute(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/flows/executor/default-authentication-flow/").mock(
        return_value=httpx.Response(200, json={"component": "ak-stage-identification"})
    )
    data = await call_tool(mcp, "authentik_flow_execute", {"slug": "default-authentication-flow"})
    assert data["component"] == "ak-stage-identification"


# --- Property Mappings ---
@respx.mock
async def test_property_mapping_list(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/propertymappings/all/").mock(
        return_value=httpx.Response(200, json={"results": [{"pk": UUID}]})
    )
    data = await call_tool(mcp, "authentik_property_mapping_list", {})
    assert data["results"][0]["pk"] == UUID


# --- Outposts ---
@respx.mock
async def test_outpost_health(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/outposts/instances/{UUID}/health/").mock(
        return_value=httpx.Response(200, json=[{"version": "2024.1", "version_outdated": False}])
    )
    data = await call_tool(mcp, "authentik_outpost_health", {"outpost_uuid": UUID})
    assert data[0]["version"] == "2024.1"


@respx.mock
async def test_outpost_update(mcp: FastMCP) -> None:
    route = respx.patch(f"{API_BASE}/outposts/instances/{UUID}/").mock(
        return_value=httpx.Response(200, json={"pk": UUID, "name": "edge"})
    )
    data = await call_tool(mcp, "authentik_outpost_update", {"outpost_uuid": UUID, "name": "edge"})
    assert data["name"] == "edge"
    assert "edge" in route.calls.last.request.content.decode()
