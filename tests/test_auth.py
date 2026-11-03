"""Test untuk pembentukan verifier OAuth (:mod:`authentik_mcp.auth`)."""

from __future__ import annotations

import pytest
from fastmcp.server.auth import AccessToken, MultiAuth
from fastmcp.server.auth.providers.introspection import IntrospectionTokenVerifier

from authentik_mcp.auth import build_token_verifier
from authentik_mcp.auth_provider import AuthentikProvider, BearerApiKeyVerifier
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


def test_returns_authentik_provider_when_oauth_proxy_enabled() -> None:
    from authentik_mcp.auth_provider import AuthentikProvider

    settings = make_settings(
        oauth_oidc_config_url=(
            "https://auth.example.com/application/o/authentik-mcp/.well-known/openid-configuration"
        ),
        oauth_client_id="client-id",
        oauth_client_secret="client-secret",
        mcp_base_url="https://mcp.example.com",
    )
    assert settings.oauth_proxy_enabled is True
    # Domain dan slug di-derive otomatis dari OIDC config URL.
    assert settings.oauth_authentik_domain == "https://auth.example.com"
    assert settings.oauth_app_slug == "authentik-mcp"

    provider = build_token_verifier(settings)
    assert isinstance(provider, AuthentikProvider)


def test_oauth_proxy_takes_priority_over_introspection() -> None:
    from authentik_mcp.auth_provider import AuthentikProvider

    settings = make_settings(
        oauth_oidc_config_url=(
            "https://auth.example.com/application/o/authentik-mcp/.well-known/openid-configuration"
        ),
        oauth_introspection_url="https://auth.example.com/application/o/introspect/",
        oauth_client_id="client-id",
        oauth_client_secret="client-secret",
        mcp_base_url="https://mcp.example.com",
    )
    assert isinstance(build_token_verifier(settings), AuthentikProvider)


# --- API key statis (MCP_API_KEY) -------------------------------------------

_OAUTH_PROXY_KW = {
    "oauth_oidc_config_url": (
        "https://auth.example.com/application/o/authentik-mcp/.well-known/openid-configuration"
    ),
    "oauth_client_id": "client-id",
    "oauth_client_secret": "client-secret",
    "mcp_base_url": "https://mcp.example.com",
}


async def test_verifier_token_cocok_mengembalikan_access_token() -> None:
    result = await BearerApiKeyVerifier(api_key="rahasia").verify_token("rahasia")
    assert isinstance(result, AccessToken)
    assert result.client_id == "api-key-client"
    assert result.scopes == []


@pytest.mark.parametrize("token", ["salah", "", "rahasia ", "RAHASIA"])
async def test_verifier_token_salah_atau_kosong_none(token: str) -> None:
    assert await BearerApiKeyVerifier(api_key="rahasia").verify_token(token) is None


@pytest.mark.parametrize("key", ["", "   "])
def test_verifier_api_key_kosong_value_error(key: str) -> None:
    with pytest.raises(ValueError):
        BearerApiKeyVerifier(api_key=key)


def test_verifier_punya_required_scopes() -> None:
    # Regresi andhit-r/odoo8-mcp#6: tanpa super().__init__() atribut ini hilang.
    assert BearerApiKeyVerifier(api_key="k").required_scopes == []


def test_api_key_saja_menghasilkan_multi_auth() -> None:
    auth = build_token_verifier(make_settings(mcp_api_key="kunci"))
    assert isinstance(auth, MultiAuth)
    assert auth.server is None
    assert len(auth.verifiers) == 1
    assert isinstance(auth.verifiers[0], BearerApiKeyVerifier)


def test_api_key_spasi_saja_dianggap_tidak_diset() -> None:
    assert build_token_verifier(make_settings(mcp_api_key="   ")) is None


def test_oauth_proxy_plus_api_key_multi_auth_dengan_server_oauth() -> None:
    auth = build_token_verifier(make_settings(mcp_api_key="kunci", **_OAUTH_PROXY_KW))
    assert isinstance(auth, MultiAuth)
    assert isinstance(auth.server, AuthentikProvider)
    assert any(isinstance(v, BearerApiKeyVerifier) for v in auth.verifiers)


def test_introspection_plus_api_key_keduanya_di_verifiers() -> None:
    auth = build_token_verifier(
        make_settings(
            mcp_api_key="kunci",
            oauth_introspection_url="https://auth.example.com/application/o/introspect/",
            oauth_client_id="client-id",
            oauth_client_secret="client-secret",
        )
    )
    assert isinstance(auth, MultiAuth)
    assert auth.server is None
    assert len(auth.verifiers) == 2
    assert isinstance(auth.verifiers[0], IntrospectionTokenVerifier)
    assert isinstance(auth.verifiers[1], BearerApiKeyVerifier)
