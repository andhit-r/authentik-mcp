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

4. **None**: bila tidak ada konfigurasi OAuth (tanpa autentikasi — lokal/stdio).
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
        AuthentikProvider, OIDCProxy, IntrospectionTokenVerifier, atau None.
    """
    if settings.oauth_proxy_enabled:
        return _build_oauth_proxy(settings)

    if settings.oidc_proxy_enabled:
        return _build_oidc_proxy(settings)

    if settings.oauth_enabled:
        return _build_introspection_verifier(settings)

    logger.warning(
        "Konfigurasi OAuth tidak lengkap — MCP server berjalan TANPA "
        "autentikasi. Jangan gunakan mode ini di produksi."
    )
    return None


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
