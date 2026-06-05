"""Tool MCP untuk mengelola Provider Authentik (CRUD per tipe).

Mendaftarkan tool: list (semua provider), get, create, update, delete untuk
seluruh tipe provider Authentik: OAuth2, LDAP, SAML, Proxy, Radius, SCIM, RAC,
SSF, WS-Federation, Google Workspace, dan Microsoft Entra.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import AuthentikClient

# Pemetaan tipe provider -> path endpoint Authentik (relatif terhadap /api/v3).
_PROVIDER_PATHS: dict[str, str] = {
    "oauth2": "/providers/oauth2/",
    "ldap": "/providers/ldap/",
    "saml": "/providers/saml/",
    "proxy": "/providers/proxy/",
    "radius": "/providers/radius/",
    "scim": "/providers/scim/",
    "rac": "/providers/rac/",
    "ssf": "/providers/ssf/",
    "wsfed": "/providers/wsfed/",
    "google_workspace": "/providers/google_workspace/",
    "microsoft_entra": "/providers/microsoft_entra/",
}

# Field yang wajib ada di payload create per tipe (selain ``name`` yang selalu
# wajib). Field non-eksplisit (mis. ``signing_key``, ``credentials``) dapat
# dikirim lewat ``extra_config``.
_PROVIDER_REQUIRED: dict[str, list[str]] = {
    "oauth2": ["authorization_flow", "invalidation_flow", "redirect_uris"],
    "saml": ["authorization_flow", "invalidation_flow", "acs_url"],
    "ldap": ["authorization_flow", "invalidation_flow"],
    "proxy": ["authorization_flow", "invalidation_flow", "external_host"],
    "radius": ["authorization_flow", "invalidation_flow"],
    "scim": ["url"],
    "rac": ["authorization_flow"],
    "ssf": ["signing_key"],
    "wsfed": ["authorization_flow", "invalidation_flow", "reply_url", "wtrealm"],
    "google_workspace": [
        "credentials",
        "default_group_email_domain",
        "delegated_subject",
    ],
    "microsoft_entra": ["client_id", "client_secret", "tenant_id"],
}


def _validate_type(provider_type: str) -> str:
    """Validasi dan normalisasi provider_type; raise ValueError bila tidak dikenal."""
    key = provider_type.strip().lower()
    if key not in _PROVIDER_PATHS:
        valid = ", ".join(sorted(_PROVIDER_PATHS))
        raise ValueError(
            f"provider_type tidak valid: {provider_type!r}. Pilih salah satu: {valid}."
        )
    return key


def register(mcp: FastMCP, client: AuthentikClient) -> None:
    """Daftarkan seluruh tool domain Provider ke server MCP."""

    @mcp.tool(tags={"providers"})
    async def authentik_provider_list(
        search: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Daftar SEMUA provider (lintas tipe) via ``/providers/all/``.

        Args:
            search: Kata kunci pencarian nama provider.
            page: Nomor halaman.
            page_size: Jumlah item per halaman.

        Returns:
            Objek paginasi berisi ``results`` (daftar provider beragam tipe).

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        params = {"search": search, "page": page, "page_size": page_size}
        return await client.get("/providers/all/", params=params)

    @mcp.tool(tags={"providers"})
    async def authentik_provider_get(provider_type: str, provider_id: int) -> dict[str, Any]:
        """Ambil detail satu provider sesuai tipenya.

        Args:
            provider_type: Salah satu kunci tipe provider (``oauth2``, ``ldap``,
                ``saml``, ``proxy``, ``radius``, ``scim``, ``rac``, ``ssf``,
                ``wsfed``, ``google_workspace``, ``microsoft_entra``).
            provider_id: pk numerik provider.

        Returns:
            Objek provider lengkap sesuai tipe (field berbeda antar tipe).

        Raises:
            ValueError: Bila ``provider_type`` tidak dikenal.
            AuthentikAPIError: 404 bila provider tidak ditemukan.
        """
        key = _validate_type(provider_type)
        return await client.get(f"{_PROVIDER_PATHS[key]}{provider_id}/")

    @mcp.tool(tags={"providers"})
    async def authentik_provider_create(
        provider_type: str,
        name: str,
        authorization_flow: str | None = None,
        invalidation_flow: str | None = None,
        redirect_uris: list[dict[str, Any]] | None = None,
        acs_url: str | None = None,
        external_host: str | None = None,
        url: str | None = None,
        extra_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Buat provider baru sesuai tipenya.

        Field wajib bervariasi per tipe (selain ``name`` yang selalu wajib):

        - **oauth2**: ``authorization_flow``, ``invalidation_flow``, ``redirect_uris``.
        - **saml**: ``authorization_flow``, ``invalidation_flow``, ``acs_url``.
        - **ldap** / **radius**: ``authorization_flow``, ``invalidation_flow``.
        - **proxy**: ``authorization_flow``, ``invalidation_flow``, ``external_host``.
        - **rac**: ``authorization_flow``.
        - **scim**: ``url`` (token via ``extra_config``).
        - **ssf**: ``signing_key`` (UUID certificate-keypair) via ``extra_config``.
        - **wsfed**: ``authorization_flow``, ``invalidation_flow``, ``reply_url``,
          ``wtrealm`` (dua terakhir via ``extra_config``).
        - **google_workspace**: ``credentials``, ``default_group_email_domain``,
          ``delegated_subject`` (semua via ``extra_config``).
        - **microsoft_entra**: ``client_id``, ``client_secret``, ``tenant_id``
          (semua via ``extra_config``).

        Args:
            provider_type: Salah satu kunci tipe provider (``oauth2``, ``ldap``,
                ``saml``, ``proxy``, ``radius``, ``scim``, ``rac``, ``ssf``,
                ``wsfed``, ``google_workspace``, ``microsoft_entra``).
            name: Nama unik provider.
            authorization_flow: UUID flow otorisasi (wajib untuk sebagian besar tipe).
            invalidation_flow: UUID flow invalidasi (logout).
            redirect_uris: *(oauth2)* Daftar redirect URI yang diizinkan.
            acs_url: *(saml)* URL ACS (Assertion Consumer Service) SP.
            external_host: *(proxy)* URL host eksternal yang diproteksi.
            url: *(scim)* Base URL endpoint SCIM tujuan.
            extra_config: Field tambahan sesuai tipe provider — termasuk field
                wajib yang tidak punya parameter eksplisit (mis. ``signing_key``,
                ``credentials``, ``client_id``, ``reply_url``, ``wtrealm``).

        Returns:
            Objek provider yang baru dibuat (termasuk ``pk``).

        Raises:
            ValueError: Bila ``provider_type`` tidak dikenal atau ada field wajib
                per tipe yang belum terisi (baik dari parameter maupun ``extra_config``).
            AuthentikAPIError: 422 bila validasi Authentik gagal.
        """
        key = _validate_type(provider_type)

        payload: dict[str, Any] = {"name": name}
        for field, value in {
            "authorization_flow": authorization_flow,
            "invalidation_flow": invalidation_flow,
            "redirect_uris": redirect_uris,
            "acs_url": acs_url,
            "external_host": external_host,
            "url": url,
        }.items():
            if value is not None:
                payload[field] = value
        if extra_config:
            payload.update(extra_config)

        # Validasi field wajib per tipe terhadap payload final.
        missing = [f for f in _PROVIDER_REQUIRED[key] if f not in payload]
        if missing:
            raise ValueError(f"Provider tipe {key!r} membutuhkan field: {', '.join(missing)}.")

        return await client.post(_PROVIDER_PATHS[key], json=payload)

    @mcp.tool(tags={"providers"})
    async def authentik_provider_update(
        provider_type: str,
        provider_id: int,
        name: str | None = None,
        authorization_flow: str | None = None,
        invalidation_flow: str | None = None,
        redirect_uris: list[dict[str, Any]] | None = None,
        acs_url: str | None = None,
        external_host: str | None = None,
        url: str | None = None,
        extra_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Perbarui sebagian field provider (PATCH). Hanya field non-None yang dikirim.

        Args:
            provider_type: Salah satu kunci tipe provider (``oauth2``, ``ldap``,
                ``saml``, ``proxy``, ``radius``, ``scim``, ``rac``, ``ssf``,
                ``wsfed``, ``google_workspace``, ``microsoft_entra``).
            provider_id: pk numerik provider.
            name: Nama baru.
            authorization_flow: UUID flow otorisasi baru.
            invalidation_flow: UUID flow invalidasi baru.
            redirect_uris: *(oauth2)* Daftar redirect URI baru.
            acs_url: *(saml)* URL ACS baru.
            external_host: *(proxy)* URL host eksternal baru.
            url: *(scim)* Base URL endpoint SCIM baru.
            extra_config: Field tambahan opsional yang ingin diubah.

        Returns:
            Objek provider setelah diperbarui.

        Raises:
            ValueError: Bila ``provider_type`` tidak dikenal atau tidak ada
                field yang diberikan.
            AuthentikAPIError: 404 bila provider tidak ditemukan.
        """
        key = _validate_type(provider_type)

        payload: dict[str, Any] = {}
        for field, value in {
            "name": name,
            "authorization_flow": authorization_flow,
            "invalidation_flow": invalidation_flow,
            "redirect_uris": redirect_uris,
            "acs_url": acs_url,
            "external_host": external_host,
            "url": url,
        }.items():
            if value is not None:
                payload[field] = value
        if extra_config:
            payload.update(extra_config)

        if not payload:
            raise ValueError("Tidak ada field yang diberikan untuk diperbarui.")

        return await client.patch(f"{_PROVIDER_PATHS[key]}{provider_id}/", json=payload)

    @mcp.tool(tags={"providers"})
    async def authentik_provider_delete(
        provider_type: str,
        provider_id: int,
    ) -> dict[str, str]:
        """Hapus provider secara permanen.

        Args:
            provider_type: Salah satu kunci tipe provider (``oauth2``, ``ldap``,
                ``saml``, ``proxy``, ``radius``, ``scim``, ``rac``, ``ssf``,
                ``wsfed``, ``google_workspace``, ``microsoft_entra``).
            provider_id: pk numerik provider.

        Returns:
            Konfirmasi penghapusan.

        Raises:
            ValueError: Bila ``provider_type`` tidak dikenal.
            AuthentikAPIError: 404 bila provider tidak ditemukan.
        """
        key = _validate_type(provider_type)
        await client.delete(f"{_PROVIDER_PATHS[key]}{provider_id}/")
        return {"status": "deleted", "provider_type": key, "provider_id": str(provider_id)}
