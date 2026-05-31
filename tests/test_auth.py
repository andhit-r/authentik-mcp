"""Test untuk pembentukan verifier OAuth (:mod:`authentik_mcp.auth`)."""

from __future__ import annotations

from fastmcp.server.auth.providers.introspection import IntrospectionTokenVerifier

from authentik_mcp.auth import build_token_verifier
from tests.conftest import make_settings


def test_returns_none_when_oauth_disabled() -> None:
    assert build_token_verifier(make_settings()) is None


def test_returns_verifier_when_oauth_enabled() -> None:
    settings = make_settings(
        oauth_introspection_url="https://auth.example.com/application/o/introspect/",
        oauth_client_id="client-id",
        oauth_client_secret="client-secret",
        oauth_required_scopes="openid profile",
    )
    verifier = build_token_verifier(settings)
    assert isinstance(verifier, IntrospectionTokenVerifier)
    assert verifier.introspection_url == settings.oauth_introspection_url
    assert verifier.client_id == "client-id"
    assert verifier.required_scopes == ["openid", "profile"]
