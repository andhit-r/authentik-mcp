"""Test untuk tool domain Group."""

from __future__ import annotations

import httpx
import respx
from fastmcp import FastMCP

from tests.conftest import API_BASE, call_tool

GUID = "11111111-1111-1111-1111-111111111111"


@respx.mock
async def test_group_list(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/core/groups/").mock(
        return_value=httpx.Response(200, json={"results": [{"name": "admins"}]})
    )
    data = await call_tool(mcp, "authentik_group_list", {})
    assert data["results"][0]["name"] == "admins"


@respx.mock
async def test_group_create(mcp: FastMCP) -> None:
    route = respx.post(f"{API_BASE}/core/groups/").mock(
        return_value=httpx.Response(201, json={"pk": GUID, "name": "team"})
    )
    data = await call_tool(mcp, "authentik_group_create", {"name": "team", "is_superuser": True})
    assert data["pk"] == GUID
    assert "is_superuser" in route.calls.last.request.content.decode()


@respx.mock
async def test_group_add_member_payload(mcp: FastMCP) -> None:
    route = respx.post(f"{API_BASE}/core/groups/{GUID}/add_user/").mock(
        return_value=httpx.Response(204)
    )
    data = await call_tool(mcp, "authentik_group_add_member", {"group_uuid": GUID, "user_id": 42})
    assert data["status"] == "member_added"
    assert '"pk":42' in route.calls.last.request.content.decode()


@respx.mock
async def test_group_remove_member(mcp: FastMCP) -> None:
    respx.post(f"{API_BASE}/core/groups/{GUID}/remove_user/").mock(return_value=httpx.Response(204))
    data = await call_tool(
        mcp, "authentik_group_remove_member", {"group_uuid": GUID, "user_id": 42}
    )
    assert data["status"] == "member_removed"


@respx.mock
async def test_group_delete(mcp: FastMCP) -> None:
    respx.delete(f"{API_BASE}/core/groups/{GUID}/").mock(return_value=httpx.Response(204))
    data = await call_tool(mcp, "authentik_group_delete", {"group_uuid": GUID})
    assert data["status"] == "deleted"
