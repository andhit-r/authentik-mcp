"""Tool MCP (baca-saja) untuk Source Authentik: daftar source dan source OAuth.

Mendaftarkan tool: ``authentik_source_list``, ``authentik_source_oauth_list``,
``authentik_source_oauth_get``, ``authentik_source_connection_list``. Tidak ada
tool tulis. Kunci ``consumer_secret`` selalu dibuang dari keluaran.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import AuthentikClient

# Kunci rahasia yang tidak boleh sampai ke client MCP.
_SECRET_KEYS = frozenset({"consumer_secret"})


def _strip_secrets(data: Any) -> Any:
    """Buang kunci rahasia secara rekursif dari balasan API.

    Args:
        data: Balasan API (dict, list, atau nilai skalar).

    Returns:
        Salinan ``data`` tanpa kunci ``consumer_secret`` di level mana pun.
    """
    if isinstance(data, dict):
        return {k: _strip_secrets(v) for k, v in data.items() if k not in _SECRET_KEYS}
    if isinstance(data, list):
        return [_strip_secrets(item) for item in data]
    return data


def register(mcp: FastMCP, client: AuthentikClient) -> None:
    """Daftarkan tool baca-saja domain Source ke server MCP.

    Args:
        mcp: Instance FastMCP.
        client: Klien Authentik bersama.
    """

    @mcp.tool(tags={"sources"})
    async def authentik_source_list(
        search: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Daftar seluruh source (semua tipe) dengan paginasi.

        Args:
            search: Kata kunci pencarian.
            page: Nomor halaman.
            page_size: Jumlah item per halaman.

        Returns:
            Objek paginasi berisi ``results`` dan ``pagination``.

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        params = {"search": search, "page": page, "page_size": page_size}
        return _strip_secrets(await client.get("/sources/all/", params=params))

    @mcp.tool(tags={"sources"})
    async def authentik_source_oauth_list(
        search: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Daftar source OAuth (mis. login Google) dengan paginasi.

        Args:
            search: Kata kunci pencarian.
            page: Nomor halaman.
            page_size: Jumlah item per halaman.

        Returns:
            Objek paginasi berisi ``results`` dan ``pagination``; ``consumer_secret``
            dibuang bila ada.

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        params = {"search": search, "page": page, "page_size": page_size}
        return _strip_secrets(await client.get("/sources/oauth/", params=params))

    @mcp.tool(tags={"sources"})
    async def authentik_source_oauth_get(slug: str) -> dict[str, Any]:
        """Ambil detail satu source OAuth berdasarkan slug.

        Args:
            slug: Slug unik source OAuth.

        Returns:
            Objek source OAuth tanpa ``consumer_secret``.

        Raises:
            AuthentikAPIError: 404 bila source tidak ditemukan.
        """
        return _strip_secrets(await client.get(f"/sources/oauth/{slug}/"))

    @mcp.tool(tags={"sources"})
    async def authentik_source_connection_list(
        source_slug: str | None = None,
        user: int | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Daftar koneksi user ke source OAuth.

        Args:
            source_slug: Filter berdasarkan slug source (query ``source__slug``).
            user: Filter berdasarkan pk user.
            page: Nomor halaman.
            page_size: Jumlah item per halaman.

        Returns:
            Objek paginasi berisi ``results`` dan ``pagination``.

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        params = {
            "source__slug": source_slug,
            "user": user,
            "page": page,
            "page_size": page_size,
        }
        return _strip_secrets(await client.get("/sources/user_connections/oauth/", params=params))
