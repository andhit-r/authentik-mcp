"""Tool MCP untuk membaca Property Mapping Authentik.

Mendaftarkan tool: list (semua property mapping) dan get berdasarkan pk via
endpoint ``/propertymappings/all/``.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import AuthentikClient


def register(mcp: FastMCP, client: AuthentikClient) -> None:
    """Daftarkan seluruh tool domain Property Mapping ke server MCP.

    Args:
        mcp: Instance FastMCP.
        client: Klien Authentik bersama.
    """

    @mcp.tool(tags={"property_mappings"})
    async def authentik_property_mapping_list(
        search: str | None = None,
        managed_isnull: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Daftar SEMUA property mapping (lintas tipe) via ``/propertymappings/all/``.

        Args:
            search: Kata kunci pencarian nama property mapping.
            managed_isnull: Bila True, hanya tampilkan mapping kustom (bukan bawaan
                yang dikelola sistem); bila False, hanya yang dikelola sistem.
            page: Nomor halaman.
            page_size: Jumlah item per halaman.

        Returns:
            Objek paginasi berisi ``results`` (daftar property mapping).

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        params = {
            "search": search,
            "managed__isnull": managed_isnull,
            "page": page,
            "page_size": page_size,
        }
        return await client.get("/propertymappings/all/", params=params)

    @mcp.tool(tags={"property_mappings"})
    async def authentik_property_mapping_get(pm_uuid: str) -> dict[str, Any]:
        """Ambil detail satu property mapping berdasarkan UUID.

        Args:
            pm_uuid: UUID (pk) property mapping.

        Returns:
            Objek property mapping lengkap (termasuk ekspresi).

        Raises:
            AuthentikAPIError: 404 bila property mapping tidak ditemukan.
        """
        return await client.get(f"/propertymappings/all/{pm_uuid}/")
