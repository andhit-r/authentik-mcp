"""Tool MCP untuk membaca Provider Authentik.

Mendaftarkan tool: list (semua provider), serta get per tipe provider
(OAuth2, LDAP, SAML, Proxy) melalui endpoint masing-masing.
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
}


def register(mcp: FastMCP, client: AuthentikClient) -> None:
    """Daftarkan seluruh tool domain Provider ke server MCP.

    Args:
        mcp: Instance FastMCP.
        client: Klien Authentik bersama.
    """

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
            provider_type: Tipe provider: ``oauth2``, ``ldap``, ``saml``, atau ``proxy``.
            provider_id: pk numerik provider.

        Returns:
            Objek provider lengkap sesuai tipe (field berbeda antar tipe).

        Raises:
            ValueError: Bila ``provider_type`` tidak dikenal.
            AuthentikAPIError: 404 bila provider tidak ditemukan.
        """
        key = provider_type.strip().lower()
        if key not in _PROVIDER_PATHS:
            valid = ", ".join(sorted(_PROVIDER_PATHS))
            raise ValueError(
                f"provider_type tidak valid: {provider_type!r}. Pilih salah satu: {valid}."
            )
        return await client.get(f"{_PROVIDER_PATHS[key]}{provider_id}/")
