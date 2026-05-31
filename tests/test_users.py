"""Test untuk tool domain User."""

from __future__ import annotations

import httpx
import pytest
import respx
from fastmcp import FastMCP

from tests.conftest import API_BASE, call_tool


@respx.mock
async def test_user_list(mcp: FastMCP) -> None:
    route = respx.get(f"{API_BASE}/core/users/").mock(
        return_value=httpx.Response(200, json={"results": [{"pk": 1, "username": "a"}]})
    )
    data = await call_tool(mcp, "authentik_user_list", {"search": "a"})
    assert data["results"][0]["username"] == "a"
    assert "search=a" in str(route.calls.last.request.url)


@respx.mock
async def test_user_get(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/core/users/5/").mock(
        return_value=httpx.Response(200, json={"pk": 5, "username": "bob"})
    )
    data = await call_tool(mcp, "authentik_user_get", {"user_id": 5})
    assert data["pk"] == 5


@respx.mock
async def test_user_get_404(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/core/users/999/").mock(return_value=httpx.Response(404))
    with pytest.raises(Exception) as exc:
        await call_tool(mcp, "authentik_user_get", {"user_id": 999})
    assert "tidak ditemukan" in str(exc.value)


@respx.mock
async def test_user_create_sends_payload(mcp: FastMCP) -> None:
    route = respx.post(f"{API_BASE}/core/users/").mock(
        return_value=httpx.Response(201, json={"pk": 10, "username": "new"})
    )
    data = await call_tool(
        mcp,
        "authentik_user_create",
        {"username": "new", "name": "New User", "email": "new@example.com"},
    )
    assert data["pk"] == 10
    body = route.calls.last.request.content.decode()
    assert "new@example.com" in body
    assert "internal" in body  # default user_type


@respx.mock
async def test_user_create_422(mcp: FastMCP) -> None:
    respx.post(f"{API_BASE}/core/users/").mock(
        return_value=httpx.Response(422, json={"username": ["sudah ada"]})
    )
    with pytest.raises(Exception) as exc:
        await call_tool(mcp, "authentik_user_create", {"username": "dup", "name": "Dup"})
    assert "Validasi gagal" in str(exc.value)


async def test_user_update_no_fields_raises(mcp: FastMCP) -> None:
    with pytest.raises(Exception) as exc:
        await call_tool(mcp, "authentik_user_update", {"user_id": 1})
    assert "Tidak ada field" in str(exc.value)


@respx.mock
async def test_user_set_password(mcp: FastMCP) -> None:
    route = respx.post(f"{API_BASE}/core/users/3/set_password/").mock(
        return_value=httpx.Response(204)
    )
    data = await call_tool(
        mcp, "authentik_user_set_password", {"user_id": 3, "password": "s3cr3t!"}
    )
    assert data["status"] == "password_set"
    assert "s3cr3t!" in route.calls.last.request.content.decode()


@respx.mock
async def test_user_activate(mcp: FastMCP) -> None:
    route = respx.patch(f"{API_BASE}/core/users/3/").mock(
        return_value=httpx.Response(200, json={"pk": 3, "is_active": True})
    )
    data = await call_tool(mcp, "authentik_user_activate", {"user_id": 3})
    assert data["is_active"] is True
    assert "true" in route.calls.last.request.content.decode().lower()


@respx.mock
async def test_user_deactivate(mcp: FastMCP) -> None:
    respx.patch(f"{API_BASE}/core/users/3/").mock(
        return_value=httpx.Response(200, json={"pk": 3, "is_active": False})
    )
    data = await call_tool(mcp, "authentik_user_deactivate", {"user_id": 3})
    assert data["is_active"] is False


@respx.mock
async def test_user_delete(mcp: FastMCP) -> None:
    respx.delete(f"{API_BASE}/core/users/7/").mock(return_value=httpx.Response(204))
    data = await call_tool(mcp, "authentik_user_delete", {"user_id": 7})
    assert data == {"status": "deleted", "user_id": "7"}
