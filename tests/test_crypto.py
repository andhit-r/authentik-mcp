"""Test untuk tool domain Crypto (certificate-key pair)."""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from fastmcp import FastMCP

from tests.conftest import API_BASE, call_tool

KP_UUID = "dddddddd-dddd-dddd-dddd-dddddddddddd"
BASE = f"{API_BASE}/crypto/certificatekeypairs"


@respx.mock
async def test_certificate_list(mcp: FastMCP) -> None:
    route = respx.get(f"{BASE}/").mock(return_value=httpx.Response(200, json={"results": []}))
    await call_tool(mcp, "authentik_certificate_list", {"search": "web"})
    assert "search=web" in str(route.calls.last.request.url)


@respx.mock
async def test_certificate_get(mcp: FastMCP) -> None:
    respx.get(f"{BASE}/{KP_UUID}/").mock(
        return_value=httpx.Response(200, json={"pk": KP_UUID, "name": "web-cert"})
    )
    data = await call_tool(mcp, "authentik_certificate_get", {"kp_uuid": KP_UUID})
    assert data["name"] == "web-cert"


@respx.mock
async def test_certificate_create(mcp: FastMCP) -> None:
    route = respx.post(f"{BASE}/").mock(
        return_value=httpx.Response(201, json={"pk": KP_UUID, "name": "imported"})
    )
    data = await call_tool(
        mcp,
        "authentik_certificate_create",
        {
            "name": "imported",
            "certificate_data": "-----BEGIN CERTIFICATE-----\nAAA\n-----END CERTIFICATE-----",
            "key_data": "-----BEGIN PRIVATE KEY-----\nBBB\n-----END PRIVATE KEY-----",
        },
    )
    assert data["pk"] == KP_UUID
    body = json.loads(route.calls.last.request.content)
    assert "BEGIN CERTIFICATE" in body["certificate_data"]
    assert "BEGIN PRIVATE KEY" in body["key_data"]


@respx.mock
async def test_certificate_generate(mcp: FastMCP) -> None:
    route = respx.post(f"{BASE}/generate/").mock(
        return_value=httpx.Response(200, json={"certificate_key_pair": KP_UUID})
    )
    data = await call_tool(
        mcp,
        "authentik_certificate_generate",
        {"common_name": "example.com", "validity_days": 365, "subject_alt_name": "www.example.com"},
    )
    assert data["certificate_key_pair"] == KP_UUID
    body = json.loads(route.calls.last.request.content)
    assert body["common_name"] == "example.com"
    assert body["validity_days"] == 365
    assert body["subject_alt_name"] == "www.example.com"


@respx.mock
async def test_certificate_update(mcp: FastMCP) -> None:
    route = respx.patch(f"{BASE}/{KP_UUID}/").mock(
        return_value=httpx.Response(200, json={"pk": KP_UUID, "name": "renamed"})
    )
    data = await call_tool(
        mcp,
        "authentik_certificate_update",
        {"kp_uuid": KP_UUID, "name": "renamed"},
    )
    assert data["name"] == "renamed"
    body = json.loads(route.calls.last.request.content)
    assert body == {"name": "renamed"}


async def test_certificate_update_no_fields(mcp: FastMCP) -> None:
    with pytest.raises(Exception) as exc:
        await call_tool(mcp, "authentik_certificate_update", {"kp_uuid": KP_UUID})
    assert "Tidak ada field" in str(exc.value)


@respx.mock
async def test_certificate_delete(mcp: FastMCP) -> None:
    respx.delete(f"{BASE}/{KP_UUID}/").mock(return_value=httpx.Response(204))
    data = await call_tool(mcp, "authentik_certificate_delete", {"kp_uuid": KP_UUID})
    assert data["status"] == "deleted"
    assert data["kp_uuid"] == KP_UUID


@respx.mock
async def test_certificate_view(mcp: FastMCP) -> None:
    respx.get(f"{BASE}/{KP_UUID}/view_certificate/").mock(
        return_value=httpx.Response(200, json={"data": "-----BEGIN CERTIFICATE-----"})
    )
    data = await call_tool(mcp, "authentik_certificate_view", {"kp_uuid": KP_UUID})
    assert "BEGIN CERTIFICATE" in data["data"]
