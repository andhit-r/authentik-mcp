"""Tool MCP untuk mengelola Provider Authentik (CRUD).

Mendaftarkan tool: list (semua provider), get, create, update, delete per tipe
provider (OAuth2, LDAP, SAML, Proxy, Radius).
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import AuthentikClient

# Pemetaan tipe provider -> path endpoint Authentik.
_PROVIDER_PATHS: dict[str, str] = {
    "oauth2": "/providers/oauth2/",
    "ldap": "/providers/ldap/",
    "saml": "/providers/saml/",
    "proxy": "/providers/proxy/",
    "radius": "/providers/radius/",
}

# Field tambahan yang wajib diisi per tipe (di luar name/authorization_flow/invalidation_flow).
_TYPE_EXTRA_REQUIRED: dict[str, list[str]] = {
    "oauth2": ["redirect_uris"],
    "saml": ["acs_url"],
    "proxy": ["external_host"],
    "ldap": [],
    "radius": [],
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
            provider_type: Tipe provider: ``oauth2``, ``ldap``, ``saml``, ``proxy``,
                atau ``radius``.
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
        authorization_flow: str,
        invalidation_flow: str,
        redirect_uris: list[dict[str, Any]] | None = None,
        acs_url: str | None = None,
        external_host: str | None = None,
        extra_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Buat provider baru.

        Field wajib bervariasi per tipe:

        - **oauth2**: ``redirect_uris`` wajib — list dict ``{"matching_mode": "strict"|"regex", "url": "..."}``
        - **saml**: ``acs_url`` wajib — URL ACS endpoint SP.
        - **proxy**: ``external_host`` wajib — URL host eksternal yang diproteksi.
        - **ldap** / **radius**: tidak ada field tambahan yang wajib.

        Args:
            provider_type: Tipe provider: ``oauth2``, ``ldap``, ``saml``, ``proxy``,
                atau ``radius``.
            name: Nama unik provider.
            authorization_flow: UUID flow otorisasi.
            invalidation_flow: UUID flow invalidasi (logout).
            redirect_uris: *(oauth2)* Daftar redirect URI yang diizinkan.
            acs_url: *(saml)* URL ACS (Assertion Consumer Service) SP.
            external_host: *(proxy)* URL host eksternal yang diproteksi.
            extra_config: Field tambahan opsional sesuai tipe provider
                (mis. ``client_id``, ``signing_kp``, ``base_dn``).

        Returns:
            Objek provider yang baru dibuat (termasuk ``pk``).

        Raises:
            ValueError: Bila ``provider_type`` tidak dikenal atau field wajib
                per tipe tidak lengkap.
            AuthentikAPIError: 422 bila validasi Authentik gagal.
        """
        key = _validate_type(provider_type)

        # Validasi field wajib per tipe.
        missing: list[str] = []
        if key == "oauth2" and redirect_uris is None:
            missing.append("redirect_uris")
        if key == "saml" and acs_url is None:
            missing.append("acs_url")
        if key == "proxy" and external_host is None:
            missing.append("external_host")
        if missing:
            raise ValueError(f"Provider tipe {key!r} membutuhkan field: {', '.join(missing)}.")

        payload: dict[str, Any] = {
            "name": name,
            "authorization_flow": authorization_flow,
            "invalidation_flow": invalidation_flow,
        }
        if redirect_uris is not None:
            payload["redirect_uris"] = redirect_uris
        if acs_url is not None:
            payload["acs_url"] = acs_url
        if external_host is not None:
            payload["external_host"] = external_host
        if extra_config:
            payload.update(extra_config)

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
        extra_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Perbarui sebagian field provider (PATCH). Hanya field non-None yang dikirim.

        Args:
            provider_type: Tipe provider: ``oauth2``, ``ldap``, ``saml``, ``proxy``,
                atau ``radius``.
            provider_id: pk numerik provider.
            name: Nama baru.
            authorization_flow: UUID flow otorisasi baru.
            invalidation_flow: UUID flow invalidasi baru.
            redirect_uris: *(oauth2)* Daftar redirect URI baru.
            acs_url: *(saml)* URL ACS baru.
            external_host: *(proxy)* URL host eksternal baru.
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
            provider_type: Tipe provider: ``oauth2``, ``ldap``, ``saml``, ``proxy``,
                atau ``radius``.
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
