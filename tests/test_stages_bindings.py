"""Test untuk tool baca-saja stage, binding flow-stage, dan device MFA."""

from __future__ import annotations

import httpx
import pytest
import respx
from fastmcp import FastMCP

from tests.conftest import API_BASE, call_tool

UUID = "11111111-2222-3333-4444-555555555555"


@respx.mock
async def test_stage_list(mcp: FastMCP) -> None:
    route = respx.get(f"{API_BASE}/stages/all/").mock(
        return_value=httpx.Response(200, json={"results": [{"pk": UUID}]})
    )
    data = await call_tool(mcp, "authentik_stage_list", {"search": "id", "page_size": 5})
    assert data["results"][0]["pk"] == UUID
    url = str(route.calls.last.request.url)
    assert "search=id" in url and "page_size=5" in url


@respx.mock
async def test_stage_identification_get(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/stages/identification/{UUID}/").mock(
        return_value=httpx.Response(200, json={"pk": UUID, "sources": []})
    )
    data = await call_tool(mcp, "authentik_stage_identification_get", {"stage_uuid": UUID})
    assert data["pk"] == UUID


@respx.mock
async def test_stage_authenticator_validate_get(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/stages/authenticator/validate/{UUID}/").mock(
        return_value=httpx.Response(200, json={"pk": UUID, "not_configured_action": "skip"})
    )
    data = await call_tool(mcp, "authentik_stage_authenticator_validate_get", {"stage_uuid": UUID})
    assert data["not_configured_action"] == "skip"


@respx.mock
async def test_stage_identification_get_404(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/stages/identification/{UUID}/").mock(return_value=httpx.Response(404))
    with pytest.raises(Exception) as exc:
        await call_tool(mcp, "authentik_stage_identification_get", {"stage_uuid": UUID})
    assert "tidak ditemukan" in str(exc.value)


@respx.mock
async def test_flow_binding_list(mcp: FastMCP) -> None:
    route = respx.get(f"{API_BASE}/flows/bindings/").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    await call_tool(mcp, "authentik_flow_binding_list", {"target": "x", "stage": UUID})
    url = str(route.calls.last.request.url)
    assert "target=x" in url and f"stage={UUID}" in url


@respx.mock
async def test_flow_binding_get(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/flows/bindings/{UUID}/").mock(
        return_value=httpx.Response(200, json={"pk": UUID, "order": 10})
    )
    data = await call_tool(mcp, "authentik_flow_binding_get", {"fsb_uuid": UUID})
    assert data["order"] == 10


@respx.mock
async def test_authenticator_admin_list(mcp: FastMCP) -> None:
    route = respx.get(f"{API_BASE}/authenticators/admin/all/").mock(
        return_value=httpx.Response(200, json=[{"pk": "1", "type": "totp"}])
    )
    await call_tool(mcp, "authentik_authenticator_admin_list", {"user": 5})
    assert "user=5" in str(route.calls.last.request.url)
