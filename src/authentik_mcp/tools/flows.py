"""Tool MCP untuk mengelola Flow Authentik (endpoint ``/flows/``).

Mendaftarkan tool: list, get, dan execute (memulai eksekusi flow).
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import AuthentikClient


def register(mcp: FastMCP, client: AuthentikClient) -> None:
    """Daftarkan seluruh tool domain Flow ke server MCP.

    Args:
        mcp: Instance FastMCP.
        client: Klien Authentik bersama.
    """

    @mcp.tool(tags={"flows"})
    async def authentik_flow_list(
        search: str | None = None,
        designation: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Daftar flow dengan filter dan paginasi.

        Args:
            search: Kata kunci pencarian (nama/slug/title).
            designation: Filter berdasarkan peruntukan flow (mis.
                ``authentication``, ``authorization``, ``enrollment``,
                ``recovery``, ``invalidation``).
            page: Nomor halaman.
            page_size: Jumlah item per halaman.

        Returns:
            Objek paginasi berisi ``results`` (daftar flow) dan ``pagination``.

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        params = {
            "search": search,
            "designation": designation,
            "page": page,
            "page_size": page_size,
        }
        return await client.get("/flows/instances/", params=params)

    @mcp.tool(tags={"flows"})
    async def authentik_flow_get(slug: str) -> dict[str, Any]:
        """Ambil detail satu flow berdasarkan slug.

        Args:
            slug: Slug unik flow.

        Returns:
            Objek flow lengkap.

        Raises:
            AuthentikAPIError: 404 bila flow tidak ditemukan.
        """
        return await client.get(f"/flows/instances/{slug}/")

    @mcp.tool(tags={"flows"})
    async def authentik_flow_execute(slug: str) -> dict[str, Any]:
        """Mulai eksekusi sebuah flow dan kembalikan challenge tahap pertama.

        Memanggil endpoint executor Authentik (``/flows/executor/{slug}/``) yang
        mengembalikan ``challenge`` untuk tahap (stage) pertama dari flow.

        Args:
            slug: Slug flow yang dieksekusi.

        Returns:
            Objek challenge tahap pertama (mis. komponen form yang harus diisi).

        Raises:
            AuthentikAPIError: 404 bila flow tidak ditemukan, atau error lain.
        """
        # query=- diperlukan oleh executor Authentik sebagai parameter awal.
        return await client.get(f"/flows/executor/{slug}/", params={"query": ""})
