"""Penyedia OAuth Proxy untuk login via Authentik.

``AuthentikProvider`` adalah subclass :class:`OAuthProxy` (FastMCP 3.x) yang
menjadikan Authentik sebagai identity provider. Dengan provider ini:

* MCP server mengekspos endpoint OAuth sendiri (``/authorize``, ``/token``,
  ``/.well-known/...``) dan menerima **Dynamic Client Registration** sehingga
  Claude.ai mendaftar otomatis — pengguna **tidak perlu** mengisi client id /
  client secret, cukup **login di Authentik**.
* ``client_id`` / ``client_secret`` upstream berada di sisi server (``.env``),
  dibuat sekali oleh admin pada OAuth2/OpenID Provider Authentik.
* Token upstream Authentik diverifikasi via JWKS; MCP server lalu menerbitkan
  JWT-nya sendiri kepada client.

Endpoint Authentik dibangun dari domain publik + slug provider:

* Authorize  : ``/application/o/authorize/`` (generik, tanpa slug)
* Token      : ``/application/o/token/`` (generik, tanpa slug)
* JWKS       : ``/application/o/<slug>/jwks/``
* Userinfo   : ``/application/o/userinfo/``
* Issuer     : ``/application/o/<slug>/``
* End-session: ``/application/o/<slug>/end-session/``

Authentik 2024+ memakai endpoint generik untuk authorize & token; slug hanya
dipakai untuk JWKS, issuer, dan end-session.
"""

from __future__ import annotations

from typing import Any

import httpx
from fastmcp.server.auth.oauth_proxy.proxy import OAuthProxy
from fastmcp.server.auth.providers.jwt import JWTVerifier
from mcp.server.auth.provider import TokenError

from .logging import get_logger

logger = get_logger(__name__)

_DEFAULT_SCOPES = ["openid", "profile", "email"]


class AuthentikProvider(OAuthProxy):
    """OAuth Proxy dengan Authentik sebagai identity provider."""

    def __init__(
        self,
        *,
        authentik_domain: str,
        application_slug: str,
        client_id: str,
        client_secret: str,
        base_url: str,
        valid_scopes: list[str] | None = None,
        allowed_usernames: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Inisialisasi provider dari konfigurasi Authentik.

        Args:
            authentik_domain: URL publik (browser-facing) Authentik, mis.
                ``https://auth.example.com``. Tanpa trailing slash.
            application_slug: Slug OAuth2/OIDC Provider di Authentik.
            client_id: Client ID dari Authentik OAuth2 Provider.
            client_secret: Client Secret dari Authentik OAuth2 Provider.
            base_url: URL publik MCP server ini (untuk OAuth metadata & callback).
            valid_scopes: Scope yang diminta saat login. Default
                ``["openid", "profile", "email"]``.
            allowed_usernames: Daftar ``preferred_username`` Authentik yang
                diizinkan (case-insensitive). Kosong/None = semua user diizinkan.
            **kwargs: Diteruskan ke ``OAuthProxy.__init__``.
        """
        base = authentik_domain.rstrip("/")
        slug = application_slug.strip("/")

        authorize_url = f"{base}/application/o/authorize/"
        token_url = f"{base}/application/o/token/"
        jwks_url = f"{base}/application/o/{slug}/jwks/"
        revoke_url = f"{base}/application/o/{slug}/end-session/"
        issuer_url = f"{base}/application/o/{slug}/"
        self._userinfo_url = f"{base}/application/o/userinfo/"

        token_verifier = JWTVerifier(jwks_uri=jwks_url, issuer=issuer_url)

        super().__init__(
            upstream_authorization_endpoint=authorize_url,
            upstream_token_endpoint=token_url,
            upstream_client_id=client_id,
            upstream_client_secret=client_secret,
            upstream_revocation_endpoint=revoke_url,
            token_verifier=token_verifier,
            base_url=base_url,
            valid_scopes=valid_scopes or _DEFAULT_SCOPES,
            **kwargs,
        )

        self._allowed_usernames: frozenset[str] = frozenset(
            u.lower().strip() for u in (allowed_usernames or []) if u.strip()
        )
        logger.debug(
            "AuthentikProvider siap — issuer: %s | allowed: %s",
            issuer_url,
            list(self._allowed_usernames) or "(semua diizinkan)",
        )

    async def _extract_upstream_claims(self, idp_tokens: dict[str, Any]) -> dict[str, Any] | None:
        """Ambil identitas pengguna dari Authentik dan validasi akses.

        Memanggil userinfo endpoint Authentik untuk identitas pengguna. Bila
        ``allowed_usernames`` dikonfigurasi dan username tidak terdaftar,
        ``TokenError`` di-raise sehingga JWT FastMCP tidak diterbitkan.
        Pemeriksaan hanya terjadi saat pertukaran authorization code / refresh.

        Args:
            idp_tokens: Response token dari Authentik (berisi ``access_token``).

        Returns:
            Dict klaim untuk disematkan di JWT FastMCP.

        Raises:
            TokenError: Bila access token tidak ada, userinfo gagal dihubungi,
                atau username tidak diizinkan.
        """
        access_token = idp_tokens.get("access_token", "")
        if not access_token:
            raise TokenError("access_denied", "Upstream access token tidak tersedia")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self._userinfo_url,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
        except httpx.RequestError as exc:
            logger.warning("Gagal menghubungi Authentik userinfo: %s", exc)
            raise TokenError(
                "server_error", "Tidak dapat memverifikasi identitas dari Authentik"
            ) from exc

        if response.status_code != 200:
            logger.warning(
                "Authentik userinfo menolak token (status=%d): %s",
                response.status_code,
                response.text[:200],
            )
            raise TokenError("access_denied", "Token Authentik tidak valid atau kedaluwarsa")

        userinfo = response.json()
        username: str = (
            (userinfo.get("preferred_username") or userinfo.get("sub", "")).lower().strip()
        )

        if not username:
            raise TokenError("access_denied", "Tidak dapat mengambil username dari Authentik")

        if self._allowed_usernames and username not in self._allowed_usernames:
            logger.warning(
                "Akses ditolak untuk user Authentik '%s' — tidak dalam daftar diizinkan",
                username,
            )
            raise TokenError(
                "access_denied",
                f"User '{username}' tidak diizinkan mengakses server ini",
            )

        logger.info("User Authentik '%s' berhasil diautentikasi", username)
        return {
            "username": username,
            "email": userinfo.get("email"),
            "name": userinfo.get("name"),
            "sub": userinfo.get("sub"),
            "groups": userinfo.get("groups", []),
        }
