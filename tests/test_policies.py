"""Test untuk tool domain Policies dan Policy Bindings."""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from fastmcp import FastMCP

from tests.conftest import API_BASE, call_tool

POLICY_UUID = "cccccccc-cccc-cccc-cccc-cccccccccccc"
BINDING_UUID = "dddddddd-dddd-dddd-dddd-dddddddddddd"
TARGET_UUID = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"


# ---------------------------------------------------------------------------
# authentik_policy_list
# ---------------------------------------------------------------------------


@respx.mock
async def test_policy_list(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/policies/all/").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    data = await call_tool(mcp, "authentik_policy_list", {})
    assert data == {"results": []}


@respx.mock
async def test_policy_list_search(mcp: FastMCP) -> None:
    route = respx.get(f"{API_BASE}/policies/all/").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    await call_tool(mcp, "authentik_policy_list", {"search": "password"})
    assert "search=password" in str(route.calls.last.request.url)


# ---------------------------------------------------------------------------
# authentik_policy_get
# ---------------------------------------------------------------------------


@respx.mock
async def test_policy_get_expression(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/policies/expression/{POLICY_UUID}/").mock(
        return_value=httpx.Response(200, json={"pk": POLICY_UUID, "name": "expr-pol"})
    )
    data = await call_tool(
        mcp,
        "authentik_policy_get",
        {"policy_type": "expression", "policy_uuid": POLICY_UUID},
    )
    assert data["pk"] == POLICY_UUID


@respx.mock
async def test_policy_get_password(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/policies/password/{POLICY_UUID}/").mock(
        return_value=httpx.Response(200, json={"pk": POLICY_UUID, "name": "pw-pol"})
    )
    data = await call_tool(
        mcp,
        "authentik_policy_get",
        {"policy_type": "password", "policy_uuid": POLICY_UUID},
    )
    assert data["name"] == "pw-pol"


async def test_policy_get_invalid_type(mcp: FastMCP) -> None:
    with pytest.raises(Exception) as exc:
        await call_tool(
            mcp,
            "authentik_policy_get",
            {"policy_type": "unknown", "policy_uuid": POLICY_UUID},
        )
    assert "policy_type tidak valid" in str(exc.value)


# ---------------------------------------------------------------------------
# authentik_policy_create
# ---------------------------------------------------------------------------


@respx.mock
async def test_policy_create_expression(mcp: FastMCP) -> None:
    route = respx.post(f"{API_BASE}/policies/expression/").mock(
        return_value=httpx.Response(201, json={"pk": POLICY_UUID, "name": "expr-pol"})
    )
    data = await call_tool(
        mcp,
        "authentik_policy_create",
        {
            "policy_type": "expression",
            "name": "expr-pol",
            "expression": "return True",
        },
    )
    assert data["pk"] == POLICY_UUID
    body = json.loads(route.calls.last.request.content)
    assert body["expression"] == "return True"
    assert body["name"] == "expr-pol"


@respx.mock
async def test_policy_create_password(mcp: FastMCP) -> None:
    route = respx.post(f"{API_BASE}/policies/password/").mock(
        return_value=httpx.Response(201, json={"pk": POLICY_UUID, "name": "pw-pol"})
    )
    data = await call_tool(
        mcp,
        "authentik_policy_create",
        {
            "policy_type": "password",
            "name": "pw-pol",
            "extra_config": {"length_min": 12, "amount_digits": 2},
        },
    )
    assert data["pk"] == POLICY_UUID
    body = json.loads(route.calls.last.request.content)
    assert body["length_min"] == 12
    assert body["amount_digits"] == 2


@respx.mock
async def test_policy_create_password_expiry(mcp: FastMCP) -> None:
    route = respx.post(f"{API_BASE}/policies/password_expiry/").mock(
        return_value=httpx.Response(201, json={"pk": POLICY_UUID, "name": "expiry-pol"})
    )
    data = await call_tool(
        mcp,
        "authentik_policy_create",
        {
            "policy_type": "password_expiry",
            "name": "expiry-pol",
            "days": 90,
        },
    )
    assert data["pk"] == POLICY_UUID
    body = json.loads(route.calls.last.request.content)
    assert body["days"] == 90


@respx.mock
async def test_policy_create_reputation(mcp: FastMCP) -> None:
    route = respx.post(f"{API_BASE}/policies/reputation/").mock(
        return_value=httpx.Response(201, json={"pk": POLICY_UUID, "name": "rep-pol"})
    )
    data = await call_tool(
        mcp,
        "authentik_policy_create",
        {
            "policy_type": "reputation",
            "name": "rep-pol",
            "extra_config": {"threshold": -5, "check_ip": True},
        },
    )
    assert data["pk"] == POLICY_UUID
    body = json.loads(route.calls.last.request.content)
    assert body["threshold"] == -5


@respx.mock
async def test_policy_create_event_matcher(mcp: FastMCP) -> None:
    route = respx.post(f"{API_BASE}/policies/event_matcher/").mock(
        return_value=httpx.Response(201, json={"pk": POLICY_UUID, "name": "ev-pol"})
    )
    data = await call_tool(
        mcp,
        "authentik_policy_create",
        {
            "policy_type": "event_matcher",
            "name": "ev-pol",
            "extra_config": {"action": "login_failed"},
        },
    )
    assert data["pk"] == POLICY_UUID
    body = json.loads(route.calls.last.request.content)
    assert body["action"] == "login_failed"


async def test_policy_create_expression_missing_expression(mcp: FastMCP) -> None:
    with pytest.raises(Exception) as exc:
        await call_tool(
            mcp,
            "authentik_policy_create",
            {"policy_type": "expression", "name": "bad"},
        )
    assert "expression" in str(exc.value)


async def test_policy_create_password_expiry_missing_days(mcp: FastMCP) -> None:
    with pytest.raises(Exception) as exc:
        await call_tool(
            mcp,
            "authentik_policy_create",
            {"policy_type": "password_expiry", "name": "bad"},
        )
    assert "days" in str(exc.value)


async def test_policy_create_invalid_type(mcp: FastMCP) -> None:
    with pytest.raises(Exception) as exc:
        await call_tool(
            mcp,
            "authentik_policy_create",
            {"policy_type": "geoip", "name": "bad"},
        )
    assert "policy_type tidak valid" in str(exc.value)


# ---------------------------------------------------------------------------
# authentik_policy_update
# ---------------------------------------------------------------------------


@respx.mock
async def test_policy_update_name(mcp: FastMCP) -> None:
    route = respx.patch(f"{API_BASE}/policies/expression/{POLICY_UUID}/").mock(
        return_value=httpx.Response(200, json={"pk": POLICY_UUID, "name": "renamed"})
    )
    data = await call_tool(
        mcp,
        "authentik_policy_update",
        {"policy_type": "expression", "policy_uuid": POLICY_UUID, "name": "renamed"},
    )
    assert data["name"] == "renamed"
    body = json.loads(route.calls.last.request.content)
    assert body == {"name": "renamed"}


@respx.mock
async def test_policy_update_expression(mcp: FastMCP) -> None:
    route = respx.patch(f"{API_BASE}/policies/expression/{POLICY_UUID}/").mock(
        return_value=httpx.Response(200, json={"pk": POLICY_UUID})
    )
    await call_tool(
        mcp,
        "authentik_policy_update",
        {
            "policy_type": "expression",
            "policy_uuid": POLICY_UUID,
            "expression": "return ak_is_group_member(request.user, name='admins')",
        },
    )
    body = json.loads(route.calls.last.request.content)
    assert "ak_is_group_member" in body["expression"]


@respx.mock
async def test_policy_update_extra_config(mcp: FastMCP) -> None:
    route = respx.patch(f"{API_BASE}/policies/password/{POLICY_UUID}/").mock(
        return_value=httpx.Response(200, json={"pk": POLICY_UUID})
    )
    await call_tool(
        mcp,
        "authentik_policy_update",
        {
            "policy_type": "password",
            "policy_uuid": POLICY_UUID,
            "extra_config": {"length_min": 16},
        },
    )
    body = json.loads(route.calls.last.request.content)
    assert body["length_min"] == 16


async def test_policy_update_no_fields(mcp: FastMCP) -> None:
    with pytest.raises(Exception) as exc:
        await call_tool(
            mcp,
            "authentik_policy_update",
            {"policy_type": "expression", "policy_uuid": POLICY_UUID},
        )
    assert "Tidak ada field" in str(exc.value)


# ---------------------------------------------------------------------------
# authentik_policy_delete
# ---------------------------------------------------------------------------


@respx.mock
async def test_policy_delete(mcp: FastMCP) -> None:
    respx.delete(f"{API_BASE}/policies/all/{POLICY_UUID}/").mock(return_value=httpx.Response(204))
    data = await call_tool(mcp, "authentik_policy_delete", {"policy_uuid": POLICY_UUID})
    assert data["status"] == "deleted"
    assert data["policy_uuid"] == POLICY_UUID


# ---------------------------------------------------------------------------
# authentik_policy_test
# ---------------------------------------------------------------------------


@respx.mock
async def test_policy_test(mcp: FastMCP) -> None:
    route = respx.post(f"{API_BASE}/policies/all/{POLICY_UUID}/test/").mock(
        return_value=httpx.Response(200, json={"passing": True, "messages": []})
    )
    data = await call_tool(
        mcp,
        "authentik_policy_test",
        {"policy_uuid": POLICY_UUID, "user_id": 5},
    )
    assert data["passing"] is True
    body = json.loads(route.calls.last.request.content)
    assert body["user"] == 5


@respx.mock
async def test_policy_test_with_context(mcp: FastMCP) -> None:
    route = respx.post(f"{API_BASE}/policies/all/{POLICY_UUID}/test/").mock(
        return_value=httpx.Response(200, json={"passing": False, "messages": ["denied"]})
    )
    ctx = {"flow_plan": {"context": {}}}
    data = await call_tool(
        mcp,
        "authentik_policy_test",
        {"policy_uuid": POLICY_UUID, "user_id": 3, "context": ctx},
    )
    assert data["passing"] is False
    body = json.loads(route.calls.last.request.content)
    assert body["context"] == ctx


# ---------------------------------------------------------------------------
# authentik_policy_binding_list
# ---------------------------------------------------------------------------


@respx.mock
async def test_policy_binding_list(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/policies/bindings/").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    data = await call_tool(mcp, "authentik_policy_binding_list", {})
    assert data == {"results": []}


@respx.mock
async def test_policy_binding_list_filter_target(mcp: FastMCP) -> None:
    route = respx.get(f"{API_BASE}/policies/bindings/").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    await call_tool(mcp, "authentik_policy_binding_list", {"target": TARGET_UUID})
    assert f"target={TARGET_UUID}" in str(route.calls.last.request.url)


# ---------------------------------------------------------------------------
# authentik_policy_binding_get
# ---------------------------------------------------------------------------


@respx.mock
async def test_policy_binding_get(mcp: FastMCP) -> None:
    respx.get(f"{API_BASE}/policies/bindings/{BINDING_UUID}/").mock(
        return_value=httpx.Response(200, json={"pk": BINDING_UUID, "order": 0})
    )
    data = await call_tool(mcp, "authentik_policy_binding_get", {"binding_uuid": BINDING_UUID})
    assert data["pk"] == BINDING_UUID


# ---------------------------------------------------------------------------
# authentik_policy_binding_create
# ---------------------------------------------------------------------------


@respx.mock
async def test_policy_binding_create_with_policy(mcp: FastMCP) -> None:
    route = respx.post(f"{API_BASE}/policies/bindings/").mock(
        return_value=httpx.Response(201, json={"pk": BINDING_UUID, "order": 0})
    )
    data = await call_tool(
        mcp,
        "authentik_policy_binding_create",
        {
            "target": TARGET_UUID,
            "order": 0,
            "policy": POLICY_UUID,
        },
    )
    assert data["pk"] == BINDING_UUID
    body = json.loads(route.calls.last.request.content)
    assert body["target"] == TARGET_UUID
    assert body["policy"] == POLICY_UUID
    assert body["order"] == 0


@respx.mock
async def test_policy_binding_create_with_group(mcp: FastMCP) -> None:
    group_uuid = "ffffffff-ffff-ffff-ffff-ffffffffffff"
    route = respx.post(f"{API_BASE}/policies/bindings/").mock(
        return_value=httpx.Response(201, json={"pk": BINDING_UUID})
    )
    await call_tool(
        mcp,
        "authentik_policy_binding_create",
        {"target": TARGET_UUID, "order": 10, "group": group_uuid},
    )
    body = json.loads(route.calls.last.request.content)
    assert body["group"] == group_uuid
    assert "policy" not in body


@respx.mock
async def test_policy_binding_create_with_user(mcp: FastMCP) -> None:
    route = respx.post(f"{API_BASE}/policies/bindings/").mock(
        return_value=httpx.Response(201, json={"pk": BINDING_UUID})
    )
    await call_tool(
        mcp,
        "authentik_policy_binding_create",
        {"target": TARGET_UUID, "order": 20, "user": 7},
    )
    body = json.loads(route.calls.last.request.content)
    assert body["user"] == 7
    assert "policy" not in body
    assert "group" not in body


async def test_policy_binding_create_no_policy_group_user(mcp: FastMCP) -> None:
    with pytest.raises(Exception) as exc:
        await call_tool(
            mcp,
            "authentik_policy_binding_create",
            {"target": TARGET_UUID, "order": 0},
        )
    assert "policy" in str(exc.value)


# ---------------------------------------------------------------------------
# authentik_policy_binding_update
# ---------------------------------------------------------------------------


@respx.mock
async def test_policy_binding_update(mcp: FastMCP) -> None:
    route = respx.patch(f"{API_BASE}/policies/bindings/{BINDING_UUID}/").mock(
        return_value=httpx.Response(200, json={"pk": BINDING_UUID, "enabled": False})
    )
    data = await call_tool(
        mcp,
        "authentik_policy_binding_update",
        {"binding_uuid": BINDING_UUID, "enabled": False},
    )
    assert data["enabled"] is False
    body = json.loads(route.calls.last.request.content)
    assert body == {"enabled": False}


async def test_policy_binding_update_no_fields(mcp: FastMCP) -> None:
    with pytest.raises(Exception) as exc:
        await call_tool(mcp, "authentik_policy_binding_update", {"binding_uuid": BINDING_UUID})
    assert "Tidak ada field" in str(exc.value)


# ---------------------------------------------------------------------------
# authentik_policy_binding_delete
# ---------------------------------------------------------------------------


@respx.mock
async def test_policy_binding_delete(mcp: FastMCP) -> None:
    respx.delete(f"{API_BASE}/policies/bindings/{BINDING_UUID}/").mock(
        return_value=httpx.Response(204)
    )
    data = await call_tool(mcp, "authentik_policy_binding_delete", {"binding_uuid": BINDING_UUID})
    assert data["status"] == "deleted"
    assert data["binding_uuid"] == BINDING_UUID
