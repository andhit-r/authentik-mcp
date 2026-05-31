"""Proteksi akses MCP server menggunakan OAuth (Authentik sebagai IdP).

FastMCP 3.x menyediakan dukungan autentikasi bawaan melalui kelas
``TokenVerifier``. Untuk opaque token yang diterbitkan Authentik, kita memakai
:class:`fastmcp.server.auth.providers.introspection.IntrospectionTokenVerifier`
yang memvalidasi Bearer token client melalui OAuth 2.0 Token Introspection
(RFC 7662) ke endpoint ``/application/o/introspect/`` milik Authentik.

Pendekatan yang dipakai: **Bearer token validation bawaan FastMCP** (bukan
middleware manual), karena versi FastMCP yang terinspeksi (3.x) mendukungnya
secara native dan lebih terintegrasi dengan alur OAuth Claude.ai.

Bila konfigurasi OAuth tidak lengkap, fungsi :func:`build_token_verifier`
mengembalikan ``None`` sehingga MCP server berjalan tanpa autentikasi (hanya
untuk pengembangan lokal).
"""

from __future__ import annotations

from fastmcp.server.auth.providers.introspection import IntrospectionTokenVerifier

from .config import Settings
from .logging import get_logger

logger = get_logger(__name__)


def build_token_verifier(settings: Settings) -> IntrospectionTokenVerifier | None:
    """Bangun verifier OAuth introspection dari konfigurasi.

    Args:
        settings: Konfigurasi aplikasi. Memakai ``oauth_introspection_url``,
            ``oauth_client_id``, ``oauth_client_secret``, ``oauth_required_scopes``,
            dan ``oauth_cache_ttl``.

    Returns:
        Instance :class:`IntrospectionTokenVerifier` bila konfigurasi OAuth
        lengkap, atau ``None`` bila autentikasi MCP dinonaktifkan.

    Notes:
        Authentik menerima autentikasi client pada endpoint introspection via
        HTTP Basic Auth (``client_secret_basic``), yang merupakan default
        verifier ini.
    """
    if not settings.oauth_enabled:
        logger.warning(
            "Konfigurasi OAuth tidak lengkap — MCP server berjalan TANPA "
            "autentikasi. Jangan gunakan mode ini di produksi."
        )
        return None

    required_scopes = settings.required_scopes_list or None
    cache_ttl = settings.oauth_cache_ttl or None

    logger.info(
        "Autentikasi MCP aktif: introspeksi token ke %s (scopes wajib: %s).",
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
