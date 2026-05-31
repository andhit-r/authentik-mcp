"""Test untuk tool domain Providers (CRUD)."""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from fastmcp import FastMCP

from tests.conftest import API_BASE, call_tool

FLOW_UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
INVAL_UUID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


# ---------------------------------------------------------------------------
# authentik_provider_list
# ---------------------------------------------------------------------------


@respx.mock
async def test_provider_list(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/providers/all/").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    data = await call_tool(mcp, "authentik_provider_list", {})
    assert data == {"results": []}


@respx.mock
async def test_provider_list_search(mcp: FastMCP) -> None:
    route = respx.get(f"{API_BASE}/providers/all/").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    await call_tool(mcp, "authentik_provider_list", {"search": "grafana"})
    assert "search=grafana" in str(route.calls.last.request.url)


# ---------------------------------------------------------------------------
# authentik_provider_get
# ---------------------------------------------------------------------------


@respx.mock
async def test_provider_get_oauth2(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/providers/oauth2/3/").mock(
        return_value=httpx.Response(200, json={"pk": 3, "name": "oauth"})
    )
    data = await call_tool(
        mcp, "authentik_provider_get", {"provider_type": "oauth2", "provider_id": 3}
    )
    assert data["pk"] == 3


@respx.mock
async def test_provider_get_ldap(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/providers/ldap/7/").mock(
        return_value=httpx.Response(200, json={"pk": 7, "name": "ldap-prov"})
    )
    data = await call_tool(
        mcp, "authentik_provider_get", {"provider_type": "ldap", "provider_id": 7}
    )
    assert data["name"] == "ldap-prov"


@respx.mock
async def test_provider_get_radius(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/providers/radius/9/").mock(
        return_value=httpx.Response(200, json={"pk": 9, "name": "radius-prov"})
    )
    data = await call_tool(
        mcp, "authentik_provider_get", {"provider_type": "radius", "provider_id": 9}
    )
    assert data["pk"] == 9


async def test_provider_get_invalid_type(mcp: FastMCP) -> None:
    with pytest.raises(Exception) as exc:
        await call_tool(
            mcp,
            "authentik_provider_get",
            {"provider_type": "unknown", "provider_id": 1},
        )
    assert "provider_type tidak valid" in str(exc.value)


# ---------------------------------------------------------------------------
# authentik_provider_create
# ---------------------------------------------------------------------------


@respx.mock
async def test_provider_create_oauth2(mcp: FastMCP) -> None:
    route = respx.post(f"{API_BASE}/providers/oauth2/").mock(
        return_value=httpx.Response(201, json={"pk": 10, "name": "my-app", "client_id": "abc"})
    )
    redirect_uris = [{"matching_mode": "strict", "url": "https://app.example.com/callback"}]
    data = await call_tool(
        mcp,
        "authentik_provider_create",
        {
            "provider_type": "oauth2",
            "name": "my-app",
            "authorization_flow": FLOW_UUID,
            "invalidation_flow": INVAL_UUID,
            "redirect_uris": redirect_uris,
        },
    )
    assert data["pk"] == 10
    body = json.loads(route.calls.last.request.content)
    assert body["name"] == "my-app"
    assert body["redirect_uris"] == redirect_uris
    assert body["authorization_flow"] == FLOW_UUID


@respx.mock
async def test_provider_create_saml(mcp: FastMCP) -> None:
    route = respx.post(f"{API_BASE}/providers/saml/").mock(
        return_value=httpx.Response(201, json={"pk": 11, "name": "saml-app"})
    )
    data = await call_tool(
        mcp,
        "authentik_provider_create",
        {
            "provider_type": "saml",
            "name": "saml-app",
            "authorization_flow": FLOW_UUID,
            "invalidation_flow": INVAL_UUID,
            "acs_url": "https://sp.example.com/saml/acs",
        },
    )
    assert data["pk"] == 11
    body = json.loads(route.calls.last.request.content)
    assert body["acs_url"] == "https://sp.example.com/saml/acs"


@respx.mock
async def test_provider_create_proxy(mcp: FastMCP) -> None:
    route = respx.post(f"{API_BASE}/providers/proxy/").mock(
        return_value=httpx.Response(201, json={"pk": 12, "name": "proxy-app"})
    )
    data = await call_tool(
        mcp,
        "authentik_provider_create",
        {
            "provider_type": "proxy",
            "name": "proxy-app",
            "authorization_flow": FLOW_UUID,
            "invalidation_flow": INVAL_UUID,
            "external_host": "https://internal.example.com",
        },
    )
    assert data["pk"] == 12
    body = json.loads(route.calls.last.request.content)
    assert body["external_host"] == "https://internal.example.com"


@respx.mock
async def test_provider_create_ldap(mcp: FastMCP) -> None:
    route = respx.post(f"{API_BASE}/providers/ldap/").mock(
        return_value=httpx.Response(201, json={"pk": 13, "name": "ldap-prov"})
    )
    data = await call_tool(
        mcp,
        "authentik_provider_create",
        {
            "provider_type": "ldap",
            "name": "ldap-prov",
            "authorization_flow": FLOW_UUID,
            "invalidation_flow": INVAL_UUID,
            "extra_config": {"base_dn": "dc=example,dc=com"},
        },
    )
    assert data["pk"] == 13
    body = json.loads(route.calls.last.request.content)
    assert body["base_dn"] == "dc=example,dc=com"


@respx.mock
async def test_provider_create_radius(mcp: FastMCP) -> None:
    route = respx.post(f"{API_BASE}/providers/radius/").mock(
        return_value=httpx.Response(201, json={"pk": 14, "name": "radius-prov"})
    )
    data = await call_tool(
        mcp,
        "authentik_provider_create",
        {
            "provider_type": "radius",
            "name": "radius-prov",
            "authorization_flow": FLOW_UUID,
            "invalidation_flow": INVAL_UUID,
            "extra_config": {"shared_secret": "s3cr3t"},
        },
    )
    assert data["pk"] == 14
    body = json.loads(route.calls.last.request.content)
    assert body["shared_secret"] == "s3cr3t"


async def test_provider_create_oauth2_missing_redirect_uris(mcp: FastMCP) -> None:
    with pytest.raises(Exception) as exc:
        await call_tool(
            mcp,
            "authentik_provider_create",
            {
                "provider_type": "oauth2",
                "name": "bad",
                "authorization_flow": FLOW_UUID,
                "invalidation_flow": INVAL_UUID,
            },
        )
    assert "redirect_uris" in str(exc.value)


async def test_provider_create_saml_missing_acs_url(mcp: FastMCP) -> None:
    with pytest.raises(Exception) as exc:
        await call_tool(
            mcp,
            "authentik_provider_create",
            {
                "provider_type": "saml",
                "name": "bad",
                "authorization_flow": FLOW_UUID,
                "invalidation_flow": INVAL_UUID,
            },
        )
    assert "acs_url" in str(exc.value)


async def test_provider_create_proxy_missing_external_host(mcp: FastMCP) -> None:
    with pytest.raises(Exception) as exc:
        await call_tool(
            mcp,
            "authentik_provider_create",
            {
                "provider_type": "proxy",
                "name": "bad",
                "authorization_flow": FLOW_UUID,
                "invalidation_flow": INVAL_UUID,
            },
        )
    assert "external_host" in str(exc.value)


async def test_provider_create_invalid_type(mcp: FastMCP) -> None:
    with pytest.raises(Exception) as exc:
        await call_tool(
            mcp,
            "authentik_provider_create",
            {
                "provider_type": "wsfed",
                "name": "bad",
                "authorization_flow": FLOW_UUID,
                "invalidation_flow": INVAL_UUID,
            },
        )
    assert "provider_type tidak valid" in str(exc.value)


# ---------------------------------------------------------------------------
# authentik_provider_update
# ---------------------------------------------------------------------------


@respx.mock
async def test_provider_update_name(mcp: FastMCP) -> None:
    route = respx.patch(f"{API_BASE}/providers/oauth2/10/").mock(
        return_value=httpx.Response(200, json={"pk": 10, "name": "renamed"})
    )
    data = await call_tool(
        mcp,
        "authentik_provider_update",
        {"provider_type": "oauth2", "provider_id": 10, "name": "renamed"},
    )
    assert data["name"] == "renamed"
    body = json.loads(route.calls.last.request.content)
    assert body == {"name": "renamed"}


@respx.mock
async def test_provider_update_redirect_uris(mcp: FastMCP) -> None:
    new_uris = [{"matching_mode": "regex", "url": "https://app.example.com/.*"}]
    route = respx.patch(f"{API_BASE}/providers/oauth2/10/").mock(
        return_value=httpx.Response(200, json={"pk": 10, "redirect_uris": new_uris})
    )
    data = await call_tool(
        mcp,
        "authentik_provider_update",
        {
            "provider_type": "oauth2",
            "provider_id": 10,
            "redirect_uris": new_uris,
        },
    )
    assert data["redirect_uris"] == new_uris
    body = json.loads(route.calls.last.request.content)
    assert body["redirect_uris"] == new_uris


@respx.mock
async def test_provider_update_extra_config(mcp: FastMCP) -> None:
    route = respx.patch(f"{API_BASE}/providers/ldap/7/").mock(
        return_value=httpx.Response(200, json={"pk": 7, "base_dn": "dc=new,dc=com"})
    )
    data = await call_tool(
        mcp,
        "authentik_provider_update",
        {
            "provider_type": "ldap",
            "provider_id": 7,
            "extra_config": {"base_dn": "dc=new,dc=com"},
        },
    )
    assert data["base_dn"] == "dc=new,dc=com"
    body = json.loads(route.calls.last.request.content)
    assert body["base_dn"] == "dc=new,dc=com"


async def test_provider_update_no_fields(mcp: FastMCP) -> None:
    with pytest.raises(Exception) as exc:
        await call_tool(
            mcp,
            "authentik_provider_update",
            {"provider_type": "oauth2", "provider_id": 10},
        )
    assert "Tidak ada field" in str(exc.value)


async def test_provider_update_invalid_type(mcp: FastMCP) -> None:
    with pytest.raises(Exception) as exc:
        await call_tool(
            mcp,
            "authentik_provider_update",
            {"provider_type": "bad", "provider_id": 1, "name": "x"},
        )
    assert "provider_type tidak valid" in str(exc.value)


# ---------------------------------------------------------------------------
# authentik_provider_delete
# ---------------------------------------------------------------------------


@respx.mock
async def test_provider_delete_oauth2(mcp: FastMCP) -> None:
    respx.delete(f"{API_BASE}/providers/oauth2/10/").mock(return_value=httpx.Response(204))
    data = await call_tool(
        mcp,
        "authentik_provider_delete",
        {"provider_type": "oauth2", "provider_id": 10},
    )
    assert data["status"] == "deleted"
    assert data["provider_type"] == "oauth2"
    assert data["provider_id"] == "10"


@respx.mock
async def test_provider_delete_saml(mcp: FastMCP) -> None:
    respx.delete(f"{API_BASE}/providers/saml/11/").mock(return_value=httpx.Response(204))
    data = await call_tool(
        mcp,
        "authentik_provider_delete",
        {"provider_type": "saml", "provider_id": 11},
    )
    assert data["status"] == "deleted"
    assert data["provider_type"] == "saml"


async def test_provider_delete_invalid_type(mcp: FastMCP) -> None:
    with pytest.raises(Exception) as exc:
        await call_tool(
            mcp,
            "authentik_provider_delete",
            {"provider_type": "wsfed", "provider_id": 1},
        )
    assert "provider_type tidak valid" in str(exc.value)
