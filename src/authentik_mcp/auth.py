"""Proteksi akses MCP server menggunakan OAuth (Authentik sebagai IdP).

FastMCP 3.x menyediakan beberapa mode proteksi. Modul ini memilih otomatis
berdasarkan konfigurasi, dengan urutan prioritas:

1. **OAuth Proxy / AuthentikProvider** (direkomendasikan untuk Claude.ai):
   MCP server mengekspos endpoint OAuth sendiri dan menerima Dynamic Client
   Registration. Claude.ai mendaftar otomatis sehingga pengguna **tidak perlu**
   mengisi client id/secret — cukup **login di Authentik**. Token upstream
   diverifikasi via JWKS. Aktif bila ``OAUTH_CLIENT_ID``, ``OAUTH_CLIENT_SECRET``,
   domain publik Authentik (dari ``OAUTH_OIDC_CONFIG_URL`` atau
   ``AUTHENTIK_OAUTH_DOMAIN``), slug provider, dan ``MCP_BASE_URL`` tersedia.

2. **OIDCProxy** (kompatibilitas): proxy berbasis OIDC discovery. Token upstream
   divalidasi via introspeksi.

3. **IntrospectionTokenVerifier** (fallback): hanya memvalidasi Bearer token
   yang sudah dipegang client.

Selain itu, **API key statis** (``MCP_API_KEY``, Bearer) dapat diaktifkan
sendiri atau digabung dengan mode di atas lewat ``MultiAuth``: mode OAuth yang
terpilih menjadi ``server`` (OAuth Proxy / OIDCProxy) atau masuk ``verifiers``
(introspection), dan API key selalu masuk ``verifiers``. Hanya API key →
``MultiAuth(verifiers=[...])``.

4. **None**: bila tidak ada konfigurasi auth sama sekali (hanya sah untuk
   stdio; transport HTTP menolak start tanpa auth — lihat
   :func:`authentik_mcp.server.run`).
"""

from __future__ import annotations

from fastmcp.server.auth.oidc_proxy import OIDCProxy
from fastmcp.server.auth.providers.introspection import IntrospectionTokenVerifier

from .config import Settings
from .logging import get_logger

logger = get_logger(__name__)


def build_token_verifier(settings: Settings):
    """Bangun auth provider dari konfigurasi (lihat docstring modul untuk urutan).

    Args:
        settings: Konfigurasi aplikasi.

    Returns:
        AuthentikProvider, OIDCProxy, IntrospectionTokenVerifier, ``MultiAuth``
        (bila ``MCP_API_KEY`` diset), atau None.
    """
    oauth = None
    if settings.oauth_proxy_enabled:
        oauth = _build_oauth_proxy(settings)
    elif settings.oidc_proxy_enabled:
        oauth = _build_oidc_proxy(settings)
    elif settings.oauth_enabled:
        oauth = _build_introspection_verifier(settings)

    if not settings.api_key_enabled:
        return oauth

    return _combine_with_api_key(settings, oauth)


def _combine_with_api_key(settings: Settings, oauth):
    """Gabungkan API key statis dengan mode OAuth terpilih lewat ``MultiAuth``.

    Args:
        settings: Konfigurasi aplikasi (``MCP_API_KEY`` harus terisi).
        oauth: Hasil mode OAuth (provider OAuth, verifier introspection, atau
            ``None`` bila tak ada OAuth).

    Returns:
        ``MultiAuth``: provider OAuth menjadi ``server``; verifier introspection
        dan API key masuk ``verifiers``.
    """
    from fastmcp.server.auth import MultiAuth, TokenVerifier

    from .auth_provider import BearerApiKeyVerifier

    verifiers: list[TokenVerifier] = []
    server = None
    if isinstance(oauth, TokenVerifier):
        verifiers.append(oauth)
    elif oauth is not None:
        server = oauth
    verifiers.append(BearerApiKeyVerifier(api_key=settings.mcp_api_key.get_secret_value().strip()))

    logger.info(
        "Autentikasi MCP aktif: API key statis (Bearer)%s.",
        " + OAuth" if oauth is not None else "",
    )
    return MultiAuth(server=server, verifiers=verifiers)


def _build_oauth_proxy(settings: Settings):
    """Bangun ``AuthentikProvider`` (OAuth Proxy + DCR) untuk login Authentik."""
    from .auth_provider import AuthentikProvider

    allowed = settings.allowed_usernames_list
    scopes = settings.required_scopes_list or None

    logger.info(
        "Autentikasi MCP aktif: AuthentikProvider (OAuth Proxy + DCR) → "
        "domain: %s | slug: %s | base_url: %s | allowed: %s | scopes: %s.",
        settings.oauth_authentik_domain,
        settings.oauth_app_slug,
        settings.mcp_base_url,
        allowed or "(semua diizinkan)",
        scopes or "default (openid profile email)",
    )

    return AuthentikProvider(
        authentik_domain=settings.oauth_authentik_domain,
        application_slug=settings.oauth_app_slug,
        client_id=settings.oauth_client_id,
        client_secret=settings.oauth_client_secret.get_secret_value(),
        base_url=settings.mcp_base_url,
        valid_scopes=scopes,
        allowed_usernames=allowed,
        require_authorization_consent="external",
    )


def _build_oidc_proxy(settings: Settings) -> OIDCProxy:
    required_scopes = settings.required_scopes_list or None
    cache_ttl = settings.oauth_cache_ttl or None

    token_verifier: IntrospectionTokenVerifier | None = None
    if settings.oauth_introspection_url:
        token_verifier = IntrospectionTokenVerifier(
            introspection_url=settings.oauth_introspection_url,
            client_id=settings.oauth_client_id,
            client_secret=settings.oauth_client_secret.get_secret_value(),
            required_scopes=required_scopes,
            cache_ttl_seconds=cache_ttl,
        )

    # Gunakan URL internal bila tersedia agar tidak bergantung resolusi DNS publik
    # dari dalam Docker. URL ini hanya untuk fetch OIDC discovery; tidak diekspos
    # ke client (client tetap melihat mcp_base_url).
    effective_config_url = settings.oauth_oidc_config_url_internal or settings.oauth_oidc_config_url

    logger.info(
        "Autentikasi MCP aktif: OIDCProxy → %s (base_url: %s, scopes: %s).",
        settings.oauth_oidc_config_url,
        settings.mcp_base_url,
        required_scopes or "tidak ada",
    )
    if settings.oauth_oidc_config_url_internal:
        logger.info(
            "OIDCProxy menggunakan URL internal untuk OIDC discovery: %s",
            effective_config_url,
        )

    proxy_kwargs: dict = {
        "config_url": effective_config_url,
        "client_id": settings.oauth_client_id,
        "client_secret": settings.oauth_client_secret.get_secret_value(),
        "base_url": settings.mcp_base_url,
    }
    if token_verifier is not None:
        proxy_kwargs["token_verifier"] = token_verifier
    else:
        proxy_kwargs["required_scopes"] = required_scopes

    return OIDCProxy(**proxy_kwargs)


def _build_introspection_verifier(settings: Settings) -> IntrospectionTokenVerifier:
    required_scopes = settings.required_scopes_list or None
    cache_ttl = settings.oauth_cache_ttl or None

    logger.info(
        "Autentikasi MCP aktif: IntrospectionTokenVerifier → %s (scopes: %s).",
        settings.oauth_introspection_url,
        required_scopes or "tidak ada",
    )
    return IntrospectionTokenVerifier(
        introspection_url=settings.oauth_introspection_url,
        client_id=settings.oauth_client_id,
        client_secret=settings.oauth_client_secret.get_secret_value(),
        required_scopes=required_scopes,
        cache_ttl_seconds=cache_ttl,
    )
