"""Tool MCP untuk mengelola Outpost Authentik (endpoint ``/outposts/instances/``).

Mendaftarkan tool: list, get, update, dan pembacaan health check.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import AuthentikClient


def register(mcp: FastMCP, client: AuthentikClient) -> None:
    """Daftarkan seluruh tool domain Outpost ke server MCP.

    Args:
        mcp: Instance FastMCP.
        client: Klien Authentik bersama.
    """

    @mcp.tool(tags={"outposts"})
    async def authentik_outpost_list(
        search: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Daftar outpost dengan filter dan paginasi.

        Args:
            search: Kata kunci pencarian nama outpost.
            page: Nomor halaman.
            page_size: Jumlah item per halaman.

        Returns:
            Objek paginasi berisi ``results`` (daftar outpost) dan ``pagination``.

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        params = {"search": search, "page": page, "page_size": page_size}
        return await client.get("/outposts/instances/", params=params)

    @mcp.tool(tags={"outposts"})
    async def authentik_outpost_get(outpost_uuid: str) -> dict[str, Any]:
        """Ambil detail satu outpost berdasarkan UUID.

        Args:
            outpost_uuid: UUID (pk) outpost.

        Returns:
            Objek outpost lengkap (termasuk konfigurasi dan provider tertaut).

        Raises:
            AuthentikAPIError: 404 bila outpost tidak ditemukan.
        """
        return await client.get(f"/outposts/instances/{outpost_uuid}/")

    @mcp.tool(tags={"outposts"})
    async def authentik_outpost_update(
        outpost_uuid: str,
        name: str | None = None,
        providers: list[int] | None = None,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Perbarui sebagian field outpost (PATCH). Hanya field non-None dikirim.

        Args:
            outpost_uuid: UUID outpost.
            name: Nama baru.
            providers: Daftar pk provider yang ditangani outpost (mengganti lama).
            config: Konfigurasi outpost (dict bebas, mis. ``authentik_host``).

        Returns:
            Objek outpost setelah diperbarui.

        Raises:
            AuthentikAPIError: 404 bila tidak ditemukan, 422 bila validasi gagal.
        """
        payload: dict[str, Any] = {}
        for key, value in {
            "name": name,
            "providers": providers,
            "config": config,
        }.items():
            if value is not None:
                payload[key] = value
        if not payload:
            raise ValueError("Tidak ada field yang diberikan untuk diperbarui.")
        return await client.patch(f"/outposts/instances/{outpost_uuid}/", json=payload)

    @mcp.tool(tags={"outposts"})
    async def authentik_outpost_health(outpost_uuid: str) -> list[dict[str, Any]]:
        """Baca status health check seluruh instance dari sebuah outpost.

        Memanggil ``/outposts/instances/{uuid}/health/`` yang melaporkan versi
        dan status koneksi tiap instance outpost yang terhubung.

        Args:
            outpost_uuid: UUID outpost.

        Returns:
            Daftar status health per instance outpost (versi, last_seen, dst).

        Raises:
            AuthentikAPIError: 404 bila outpost tidak ditemukan.
        """
        return await client.get(f"/outposts/instances/{outpost_uuid}/health/")
