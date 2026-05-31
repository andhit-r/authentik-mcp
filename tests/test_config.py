"""Test untuk modul konfigurasi (:mod:`authentik_mcp.config`)."""

from __future__ import annotations

import pytest

from authentik_mcp.config import Settings
from tests.conftest import make_settings


def test_api_base_url_strips_trailing_slash() -> None:
    s = make_settings(authentik_url="https://auth.example.com/")
    assert s.authentik_url == "https://auth.example.com"
    assert s.api_base_url == "https://auth.example.com/api/v3"


def test_oauth_enabled_false_when_incomplete() -> None:
    s = make_settings()
    assert s.oauth_enabled is False


def test_oauth_enabled_true_when_complete() -> None:
    s = make_settings(
        oauth_introspection_url="https://auth.example.com/application/o/introspect/",
        oauth_client_id="cid",
        oauth_client_secret="secret",
    )
    assert s.oauth_enabled is True


def test_required_scopes_parsing() -> None:
    s = make_settings(oauth_required_scopes="openid profile  email")
    assert s.required_scopes_list == ["openid", "profile", "email"]


def test_require_api_config_raises_when_missing() -> None:
    s = make_settings(authentik_url="", authentik_api_token="")
    with pytest.raises(ValueError) as exc:
        s.require_api_config()
    assert "AUTHENTIK_URL" in str(exc.value)
    assert "AUTHENTIK_API_TOKEN" in str(exc.value)


def test_invalid_transport_rejected() -> None:
    with pytest.raises(ValueError):
        Settings(_env_file=None, mcp_transport="grpc")
