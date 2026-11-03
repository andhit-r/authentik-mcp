"""Test guard gagal-tertutup transport HTTP pada :func:`authentik_mcp.server.run`."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from authentik_mcp.server import run
from tests.conftest import make_settings


def test_http_tanpa_auth_value_error_dan_tidak_listen() -> None:
    settings = make_settings(mcp_transport="http")
    with patch("fastmcp.FastMCP.run") as mock_run, pytest.raises(ValueError, match="MCP_API_KEY"):
        run(settings)
    mock_run.assert_not_called()


def test_http_dengan_api_key_start() -> None:
    settings = make_settings(mcp_transport="http", mcp_api_key="kunci")
    with patch("fastmcp.FastMCP.run") as mock_run:
        run(settings)
    mock_run.assert_called_once()
    assert mock_run.call_args.kwargs["transport"] == "http"


def test_stdio_tanpa_auth_tidak_melempar() -> None:
    settings = make_settings(mcp_transport="stdio", mcp_api_key="diabaikan")
    with patch("fastmcp.FastMCP.run") as mock_run:
        run(settings)
    mock_run.assert_called_once_with(transport="stdio")


def test_stdio_tanpa_apa_pun_tidak_melempar() -> None:
    with patch("fastmcp.FastMCP.run") as mock_run:
        run(make_settings(mcp_transport="stdio"))
    mock_run.assert_called_once_with(transport="stdio")
