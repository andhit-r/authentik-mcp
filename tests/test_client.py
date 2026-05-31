"""Test untuk klien HTTP Authentik (:mod:`authentik_mcp.client`).

Mencakup happy path, penanganan error HTTP (401, 404, 422, 500), error jaringan,
timeout, dan respons 204 No Content.
"""

from __future__ import annotations

import httpx
import pytest
import respx

from authentik_mcp.client import AuthentikAPIError, AuthentikClient
from tests.conftest import API_BASE


@respx.mock
async def test_get_happy_path(client: AuthentikClient) -> None:
    route = respx.get(f"{API_BASE}/core/users/").mock(
        return_value=httpx.Response(200, json={"results": [{"pk": 1}]})
    )
    data = await client.get("/core/users/")
    assert data == {"results": [{"pk": 1}]}
    assert route.called


@respx.mock
async def test_authorization_header_sent(client: AuthentikClient) -> None:
    route = respx.get(f"{API_BASE}/core/users/").mock(return_value=httpx.Response(200, json={}))
    await client.get("/core/users/")
    request = route.calls.last.request
    assert request.headers["Authorization"] == "Bearer test-token"


@respx.mock
async def test_params_none_dropped(client: AuthentikClient) -> None:
    route = respx.get(f"{API_BASE}/core/users/").mock(return_value=httpx.Response(200, json={}))
    await client.get("/core/users/", params={"search": None, "page": 2})
    url = str(route.calls.last.request.url)
    assert "search" not in url
    assert "page=2" in url


@respx.mock
async def test_204_returns_none(client: AuthentikClient) -> None:
    respx.delete(f"{API_BASE}/core/users/1/").mock(return_value=httpx.Response(204))
    assert await client.delete("/core/users/1/") is None


@respx.mock
async def test_401_raises_with_hint(client: AuthentikClient) -> None:
    respx.get(f"{API_BASE}/core/users/").mock(
        return_value=httpx.Response(401, json={"detail": "Invalid token"})
    )
    with pytest.raises(AuthentikAPIError) as exc:
        await client.get("/core/users/")
    assert exc.value.status_code == 401
    assert "Tidak terautentikasi" in str(exc.value)


@respx.mock
async def test_404_raises_with_hint(client: AuthentikClient) -> None:
    respx.get(f"{API_BASE}/core/users/999/").mock(return_value=httpx.Response(404))
    with pytest.raises(AuthentikAPIError) as exc:
        await client.get("/core/users/999/")
    assert exc.value.status_code == 404
    assert "tidak ditemukan" in str(exc.value)


@respx.mock
async def test_422_includes_detail(client: AuthentikClient) -> None:
    respx.post(f"{API_BASE}/core/users/").mock(
        return_value=httpx.Response(422, json={"username": ["sudah ada"]})
    )
    with pytest.raises(AuthentikAPIError) as exc:
        await client.post("/core/users/", json={"username": "dup"})
    assert exc.value.status_code == 422
    assert "username" in str(exc.value)


@respx.mock
async def test_500_raises(client: AuthentikClient) -> None:
    respx.get(f"{API_BASE}/core/users/").mock(return_value=httpx.Response(500))
    with pytest.raises(AuthentikAPIError) as exc:
        await client.get("/core/users/")
    assert exc.value.status_code == 500


@respx.mock
async def test_network_error_raises(client: AuthentikClient) -> None:
    respx.get(f"{API_BASE}/core/users/").mock(side_effect=httpx.ConnectError("connection refused"))
    with pytest.raises(AuthentikAPIError) as exc:
        await client.get("/core/users/")
    assert "Gagal terhubung" in str(exc.value)


@respx.mock
async def test_timeout_raises(client: AuthentikClient) -> None:
    respx.get(f"{API_BASE}/core/users/").mock(side_effect=httpx.ReadTimeout("timed out"))
    with pytest.raises(AuthentikAPIError) as exc:
        await client.get("/core/users/")
    assert "Timeout" in str(exc.value)
