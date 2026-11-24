"""Test untuk tool domain Brand (``/core/brands/``)."""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from fastmcp import FastMCP

from tests.conftest import API_BASE, call_tool

UUID = "11111111-1111-1111-1111-111111111111"
URL = f"{API_BASE}/core/brands/"


async def test_tool_brand_terdaftar(mcp: FastMCP) -> None:
    names = {t.name for t in await mcp.list_tools()}
    assert {
        "authentik_brand_list",
        "authentik_brand_get",
        "authentik_brand_create",
        "authentik_brand_update",
        "authentik_brand_delete",
    } <= names


@respx.mock
async def test_brand_list_filter(mcp: FastMCP) -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(200, json={"results": []}))
    await call_tool(mcp, "authentik_brand_list", {"domain": "a.example", "default": True})
    url = str(route.calls.last.request.url)
    assert "domain=a.example" in url
    assert "default=true" in url


@respx.mock
async def test_brand_get(mcp: FastMCP) -> None:
    respx.get(f"{URL}{UUID}/").mock(return_value=httpx.Response(200, json={"brand_uuid": UUID}))
    data = await call_tool(mcp, "authentik_brand_get", {"brand_uuid": UUID})
    assert data["brand_uuid"] == UUID


@respx.mock
async def test_brand_get_404(mcp: FastMCP) -> None:
    respx.get(f"{URL}{UUID}/").mock(return_value=httpx.Response(404))
    with pytest.raises(Exception) as exc:
        await call_tool(mcp, "authentik_brand_get", {"brand_uuid": UUID})
    assert "tidak ditemukan" in str(exc.value)


@respx.mock
async def test_brand_create_minimal(mcp: FastMCP) -> None:
    route = respx.post(URL).mock(return_value=httpx.Response(201, json={"domain": "a"}))
    await call_tool(mcp, "authentik_brand_create", {"domain": "a"})
    assert json.loads(route.calls.last.request.content) == {"domain": "a"}


@respx.mock
async def test_brand_create_lengkap(mcp: FastMCP) -> None:
    route = respx.post(URL).mock(return_value=httpx.Response(201, json={}))
    args = {
        "domain": "a",
        "branding_title": "T",
        "flow_authentication": UUID,
        "web_certificate": UUID,
        "attributes": {"k": "v"},
    }
    await call_tool(mcp, "authentik_brand_create", args)
    assert json.loads(route.calls.last.request.content) == args


@respx.mock
async def test_brand_update_patch_parsial(mcp: FastMCP) -> None:
    route = respx.patch(f"{URL}{UUID}/").mock(return_value=httpx.Response(200, json={}))
    await call_tool(mcp, "authentik_brand_update", {"brand_uuid": UUID, "branding_title": "B"})
    req = route.calls.last.request
    assert req.method == "PATCH"
    assert json.loads(req.content) == {"branding_title": "B"}


@respx.mock
async def test_brand_update_clear_fields(mcp: FastMCP) -> None:
    route = respx.patch(f"{URL}{UUID}/").mock(return_value=httpx.Response(200, json={}))
    await call_tool(
        mcp, "authentik_brand_update", {"brand_uuid": UUID, "clear_fields": ["flow_recovery"]}
    )
    assert json.loads(route.calls.last.request.content) == {"flow_recovery": None}


@respx.mock
async def test_brand_update_clear_non_nullable(mcp: FastMCP) -> None:
    with pytest.raises(Exception) as exc:
        await call_tool(
            mcp, "authentik_brand_update", {"brand_uuid": UUID, "clear_fields": ["domain"]}
        )
    assert "domain" in str(exc.value)
    assert respx.calls.call_count == 0


@respx.mock
async def test_brand_update_kosong(mcp: FastMCP) -> None:
    with pytest.raises(Exception) as exc:
        await call_tool(mcp, "authentik_brand_update", {"brand_uuid": UUID})
    assert "Tidak ada field" in str(exc.value)
    assert respx.calls.call_count == 0


@respx.mock
async def test_brand_delete(mcp: FastMCP) -> None:
    respx.delete(f"{URL}{UUID}/").mock(return_value=httpx.Response(204))
    data = await call_tool(mcp, "authentik_brand_delete", {"brand_uuid": UUID})
    assert data == {"status": "deleted", "brand_uuid": UUID}
