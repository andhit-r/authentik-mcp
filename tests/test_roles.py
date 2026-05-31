"""Test untuk tool domain RBAC/Roles."""

from __future__ import annotations

import httpx
import pytest
import respx
from fastmcp import FastMCP

from tests.conftest import API_BASE, call_tool

ROLE_UUID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


# ── Role CRUD ──────────────────────────────────────────────────────────────


@respx.mock
async def test_role_list(mcp: FastMCP) -> None:
    route = respx.get(f"{API_BASE}/core/roles/").mock(
        return_value=httpx.Response(200, json={"results": [{"pk": ROLE_UUID, "name": "admin"}]})
    )
    data = await call_tool(mcp, "authentik_role_list", {"search": "admin"})
    assert data["results"][0]["name"] == "admin"
    assert "search=admin" in str(route.calls.last.request.url)


@respx.mock
async def test_role_get(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/core/roles/{ROLE_UUID}/").mock(
        return_value=httpx.Response(200, json={"pk": ROLE_UUID, "name": "admin"})
    )
    data = await call_tool(mcp, "authentik_role_get", {"role_uuid": ROLE_UUID})
    assert data["pk"] == ROLE_UUID


@respx.mock
async def test_role_get_404(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/core/roles/{ROLE_UUID}/").mock(return_value=httpx.Response(404))
    with pytest.raises(Exception) as exc:
        await call_tool(mcp, "authentik_role_get", {"role_uuid": ROLE_UUID})
    assert "tidak ditemukan" in str(exc.value)


@respx.mock
async def test_role_create(mcp: FastMCP) -> None:
    route = respx.post(f"{API_BASE}/core/roles/").mock(
        return_value=httpx.Response(201, json={"pk": ROLE_UUID, "name": "viewer"})
    )
    data = await call_tool(mcp, "authentik_role_create", {"name": "viewer"})
    assert data["pk"] == ROLE_UUID
    assert "viewer" in route.calls.last.request.content.decode()


@respx.mock
async def test_role_create_422(mcp: FastMCP) -> None:
    respx.post(f"{API_BASE}/core/roles/").mock(
        return_value=httpx.Response(422, json={"name": ["sudah ada"]})
    )
    with pytest.raises(Exception) as exc:
        await call_tool(mcp, "authentik_role_create", {"name": "dup"})
    assert "Validasi gagal" in str(exc.value)


@respx.mock
async def test_role_update(mcp: FastMCP) -> None:
    route = respx.patch(f"{API_BASE}/core/roles/{ROLE_UUID}/").mock(
        return_value=httpx.Response(200, json={"pk": ROLE_UUID, "name": "superadmin"})
    )
    data = await call_tool(
        mcp, "authentik_role_update", {"role_uuid": ROLE_UUID, "name": "superadmin"}
    )
    assert data["name"] == "superadmin"
    assert "superadmin" in route.calls.last.request.content.decode()


@respx.mock
async def test_role_delete(mcp: FastMCP) -> None:
    respx.delete(f"{API_BASE}/core/roles/{ROLE_UUID}/").mock(return_value=httpx.Response(204))
    data = await call_tool(mcp, "authentik_role_delete", {"role_uuid": ROLE_UUID})
    assert data == {"status": "deleted", "role_uuid": ROLE_UUID}


@respx.mock
async def test_role_used_by(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/core/roles/{ROLE_UUID}/used_by/").mock(
        return_value=httpx.Response(
            200, json=[{"app": "authentik_core", "model_name": "user", "pk": "1"}]
        )
    )
    data = await call_tool(mcp, "authentik_role_used_by", {"role_uuid": ROLE_UUID})
    assert data[0]["model_name"] == "user"


# ── Katalog permission sistem ───────────────────────────────────────────────


@respx.mock
async def test_rbac_permission_list(mcp: FastMCP) -> None:
    route = respx.get(f"{API_BASE}/rbac/permissions/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {"id": 1, "name": "Can view application", "codename": "view_application"}
                ]
            },
        )
    )
    data = await call_tool(mcp, "authentik_rbac_permission_list", {"codename": "view_application"})
    assert data["results"][0]["codename"] == "view_application"
    assert "view_application" in str(route.calls.last.request.url)


# ── Permission yang di-assign ke Role ───────────────────────────────────────


@respx.mock
async def test_rbac_role_permission_list(mcp: FastMCP) -> None:
    route = respx.get(f"{API_BASE}/rbac/permissions/assigned_by_roles/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "id": 10,
                        "role": ROLE_UUID,
                        "permission": "view_application",
                    }
                ]
            },
        )
    )
    data = await call_tool(mcp, "authentik_rbac_role_permission_list", {"role_uuid": ROLE_UUID})
    assert data["results"][0]["id"] == 10
    assert ROLE_UUID in str(route.calls.last.request.url)


@respx.mock
async def test_rbac_role_assign_permission_global(mcp: FastMCP) -> None:
    route = respx.post(f"{API_BASE}/rbac/permissions/assigned_by_roles/assign/").mock(
        return_value=httpx.Response(200, json={})
    )
    await call_tool(
        mcp,
        "authentik_rbac_role_assign_permission",
        {"role_uuid": ROLE_UUID, "permissions": ["view_application", "add_application"]},
    )
    body = route.calls.last.request.content.decode()
    assert ROLE_UUID in body
    assert "view_application" in body
    assert "model" not in body


@respx.mock
async def test_rbac_role_assign_permission_object_level(mcp: FastMCP) -> None:
    route = respx.post(f"{API_BASE}/rbac/permissions/assigned_by_roles/assign/").mock(
        return_value=httpx.Response(200, json={})
    )
    await call_tool(
        mcp,
        "authentik_rbac_role_assign_permission",
        {
            "role_uuid": ROLE_UUID,
            "permissions": ["view_application"],
            "model": "authentik_core.application",
            "object_pk": "42",
        },
    )
    body = route.calls.last.request.content.decode()
    assert "authentik_core.application" in body
    assert "42" in body


@respx.mock
async def test_rbac_role_unassign_permission(mcp: FastMCP) -> None:
    respx.delete(f"{API_BASE}/rbac/permissions/assigned_by_roles/10/").mock(
        return_value=httpx.Response(204)
    )
    data = await call_tool(mcp, "authentik_rbac_role_unassign_permission", {"permission_id": 10})
    assert data == {"status": "unassigned", "permission_id": "10"}


# ── Permission yang di-assign ke User ───────────────────────────────────────


@respx.mock
async def test_rbac_user_permission_list(mcp: FastMCP) -> None:
    route = respx.get(f"{API_BASE}/rbac/permissions/assigned_by_users/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"id": 20, "user": 5, "permission": "view_token"}]},
        )
    )
    data = await call_tool(mcp, "authentik_rbac_user_permission_list", {"user_id": 5})
    assert data["results"][0]["id"] == 20
    assert "user=5" in str(route.calls.last.request.url)


@respx.mock
async def test_rbac_user_assign_permission_global(mcp: FastMCP) -> None:
    route = respx.post(f"{API_BASE}/rbac/permissions/assigned_by_users/assign/").mock(
        return_value=httpx.Response(200, json={})
    )
    await call_tool(
        mcp,
        "authentik_rbac_user_assign_permission",
        {"user_id": 5, "permissions": ["view_token"]},
    )
    body = route.calls.last.request.content.decode()
    assert '"user": 5' in body or '"user":5' in body
    assert "view_token" in body


@respx.mock
async def test_rbac_user_assign_permission_object_level(mcp: FastMCP) -> None:
    route = respx.post(f"{API_BASE}/rbac/permissions/assigned_by_users/assign/").mock(
        return_value=httpx.Response(200, json={})
    )
    await call_tool(
        mcp,
        "authentik_rbac_user_assign_permission",
        {
            "user_id": 5,
            "permissions": ["view_token"],
            "model": "authentik_core.token",
            "object_pk": "my-token",
        },
    )
    body = route.calls.last.request.content.decode()
    assert "authentik_core.token" in body
    assert "my-token" in body


@respx.mock
async def test_rbac_user_unassign_permission(mcp: FastMCP) -> None:
    respx.delete(f"{API_BASE}/rbac/permissions/assigned_by_users/20/").mock(
        return_value=httpx.Response(204)
    )
    data = await call_tool(mcp, "authentik_rbac_user_unassign_permission", {"permission_id": 20})
    assert data == {"status": "unassigned", "permission_id": "20"}
