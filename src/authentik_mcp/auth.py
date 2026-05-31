"""Proteksi akses MCP server menggunakan OAuth (Authentik sebagai IdP).

FastMCP 3.x menyediakan dua mode proteksi:

1. **OIDCProxy** (direkomendasikan untuk Claude.ai): bertindak sebagai OAuth
   Authorization Server proxy ke Authentik. MCP server mengekspos endpoint
   ``/authorize``, ``/token``, dan ``/.well-known/oauth-authorization-server``
   sendiri — Claude.ai redirect ke sini, lalu MCP server mem-proxy ke Authentik.
   Token upstream Authentik divalidasi via introspeksi; MCP server menerbitkan
   JWT-nya sendiri ke client.

2. **IntrospectionTokenVerifier** (fallback): hanya memvalidasi Bearer token
   yang sudah dipegang client. Cocok bila client sudah memiliki token Authentik
   sendiri (bukan untuk alur OAuth Claude.ai).

Bila ``OAUTH_OIDC_CONFIG_URL`` dan ``MCP_BASE_URL`` diisi, mode OIDCProxy
diaktifkan. Bila hanya ``OAUTH_INTROSPECTION_URL`` yang diisi, fallback ke
IntrospectionTokenVerifier. Bila tidak ada, server berjalan tanpa autentikasi.
"""

from __future__ import annotations

from fastmcp.server.auth.oidc_proxy import OIDCProxy
from fastmcp.server.auth.providers.introspection import IntrospectionTokenVerifier

from .config import Settings
from .logging import get_logger

logger = get_logger(__name__)


def build_token_verifier(
    settings: Settings,
) -> OIDCProxy | IntrospectionTokenVerifier | None:
    """Bangun auth provider dari konfigurasi.

    Prioritas:
    1. OIDCProxy bila ``OAUTH_OIDC_CONFIG_URL`` + ``MCP_BASE_URL`` tersedia.
    2. IntrospectionTokenVerifier bila hanya ``OAUTH_INTROSPECTION_URL`` tersedia.
    3. None bila tidak ada konfigurasi OAuth (tanpa autentikasi).

    Args:
        settings: Konfigurasi aplikasi.

    Returns:
        OIDCProxy, IntrospectionTokenVerifier, atau None.
    """
    if settings.oidc_proxy_enabled:
        return _build_oidc_proxy(settings)

    if settings.oauth_enabled:
        return _build_introspection_verifier(settings)

    logger.warning(
        "Konfigurasi OAuth tidak lengkap — MCP server berjalan TANPA "
        "autentikasi. Jangan gunakan mode ini di produksi."
    )
    return None


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

    logger.info(
        "Autentikasi MCP aktif: OIDCProxy → %s (base_url: %s, scopes: %s).",
        settings.oauth_oidc_config_url,
        settings.mcp_base_url,
        required_scopes or "tidak ada",
    )

    proxy_kwargs: dict = {
        "config_url": settings.oauth_oidc_config_url,
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
