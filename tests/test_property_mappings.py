"""Test untuk tool domain Property Mappings (CRUD per tipe)."""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from fastmcp import FastMCP

from tests.conftest import API_BASE, call_tool

PM_UUID = "cccccccc-cccc-cccc-cccc-cccccccccccc"


@respx.mock
async def test_property_mapping_list(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/propertymappings/all/").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    data = await call_tool(mcp, "authentik_property_mapping_list", {})
    assert data == {"results": []}


@respx.mock
async def test_property_mapping_get(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/propertymappings/all/{PM_UUID}/").mock(
        return_value=httpx.Response(200, json={"pk": PM_UUID, "name": "scope-email"})
    )
    data = await call_tool(mcp, "authentik_property_mapping_get", {"pm_uuid": PM_UUID})
    assert data["name"] == "scope-email"


@respx.mock
async def test_property_mapping_create_scope(mcp: FastMCP) -> None:
    route = respx.post(f"{API_BASE}/propertymappings/provider/scope/").mock(
        return_value=httpx.Response(201, json={"pk": PM_UUID, "name": "scope-email"})
    )
    data = await call_tool(
        mcp,
        "authentik_property_mapping_create",
        {
            "mapping_type": "provider_scope",
            "name": "scope-email",
            "expression": "return {'email': request.user.email}",
            "scope_name": "email",
        },
    )
    assert data["pk"] == PM_UUID
    body = json.loads(route.calls.last.request.content)
    assert body["scope_name"] == "email"
    assert body["expression"].startswith("return")


@respx.mock
async def test_property_mapping_create_source_ldap(mcp: FastMCP) -> None:
    route = respx.post(f"{API_BASE}/propertymappings/source/ldap/").mock(
        return_value=httpx.Response(201, json={"pk": PM_UUID, "name": "ldap-map"})
    )
    data = await call_tool(
        mcp,
        "authentik_property_mapping_create",
        {
            "mapping_type": "source_ldap",
            "name": "ldap-map",
            "expression": "return ldap.get('mail')",
        },
    )
    assert data["pk"] == PM_UUID
    body = json.loads(route.calls.last.request.content)
    assert body["name"] == "ldap-map"


async def test_property_mapping_create_scope_missing_scope_name(mcp: FastMCP) -> None:
    with pytest.raises(Exception) as exc:
        await call_tool(
            mcp,
            "authentik_property_mapping_create",
            {
                "mapping_type": "provider_scope",
                "name": "bad",
                "expression": "return {}",
            },
        )
    assert "scope_name" in str(exc.value)


async def test_property_mapping_create_invalid_type(mcp: FastMCP) -> None:
    with pytest.raises(Exception) as exc:
        await call_tool(
            mcp,
            "authentik_property_mapping_create",
            {"mapping_type": "bogus", "name": "x", "expression": "return {}"},
        )
    assert "mapping_type tidak valid" in str(exc.value)


@respx.mock
async def test_property_mapping_update(mcp: FastMCP) -> None:
    route = respx.patch(f"{API_BASE}/propertymappings/provider/saml/{PM_UUID}/").mock(
        return_value=httpx.Response(200, json={"pk": PM_UUID, "name": "renamed"})
    )
    data = await call_tool(
        mcp,
        "authentik_property_mapping_update",
        {"mapping_type": "provider_saml", "pm_uuid": PM_UUID, "name": "renamed"},
    )
    assert data["name"] == "renamed"
    body = json.loads(route.calls.last.request.content)
    assert body == {"name": "renamed"}


async def test_property_mapping_update_no_fields(mcp: FastMCP) -> None:
    with pytest.raises(Exception) as exc:
        await call_tool(
            mcp,
            "authentik_property_mapping_update",
            {"mapping_type": "provider_scope", "pm_uuid": PM_UUID},
        )
    assert "Tidak ada field" in str(exc.value)


@respx.mock
async def test_property_mapping_delete(mcp: FastMCP) -> None:
    respx.delete(f"{API_BASE}/propertymappings/all/{PM_UUID}/").mock(
        return_value=httpx.Response(204)
    )
    data = await call_tool(mcp, "authentik_property_mapping_delete", {"pm_uuid": PM_UUID})
    assert data["status"] == "deleted"
    assert data["pm_uuid"] == PM_UUID


@respx.mock
async def test_property_mapping_test(mcp: FastMCP) -> None:
    route = respx.post(f"{API_BASE}/propertymappings/all/{PM_UUID}/test/").mock(
        return_value=httpx.Response(200, json={"result": "ok", "successful": True})
    )
    data = await call_tool(
        mcp,
        "authentik_property_mapping_test",
        {"pm_uuid": PM_UUID, "user_id": 1},
    )
    assert data["successful"] is True
    body = json.loads(route.calls.last.request.content)
    assert body["user"] == 1
