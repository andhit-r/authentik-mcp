"""Test untuk dokumentasi OpenAPI/Swagger dan rute kustom."""

from __future__ import annotations

from fastmcp import FastMCP

from authentik_mcp.docs import build_openapi_spec


async def test_openapi_spec_has_all_tools(mcp: FastMCP) -> None:
    spec = await build_openapi_spec(mcp, "1.0.0")
    assert spec["openapi"] == "3.1.0"
    assert spec["info"]["version"] == "1.0.0"
    # Setiap tool harus terdokumentasi sebagai satu path POST.
    tools = await mcp.list_tools()
    assert len(spec["paths"]) == len(tools)
    assert "/tools/authentik_user_list" in spec["paths"]
    op = spec["paths"]["/tools/authentik_user_list"]["post"]
    assert op["operationId"] == "authentik_user_list"
    assert "users" in op["tags"]
    assert "schema" in op["requestBody"]["content"]["application/json"]
