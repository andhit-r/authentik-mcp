"""Tool MCP (baca-saja) untuk Stage Authentik (endpoint ``/stages/``).

Mendaftarkan tool: ``authentik_stage_list``, ``authentik_stage_identification_get``,
dan ``authentik_stage_authenticator_validate_get``. Tidak ada tool tulis.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import AuthentikClient


def register(mcp: FastMCP, client: AuthentikClient) -> None:
    """Daftarkan tool baca-saja domain Stage ke server MCP.

    Args:
        mcp: Instance FastMCP.
        client: Klien Authentik bersama.
    """

    @mcp.tool(tags={"stages"})
    async def authentik_stage_list(
        search: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Daftar seluruh stage (semua jenis) dengan paginasi.

        Args:
            search: Kata kunci pencarian.
            page: Nomor halaman.
            page_size: Jumlah item per halaman.

        Returns:
            Objek paginasi berisi ``results`` (tiap stage memuat jenis/komponennya)
            dan ``pagination``.

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        params = {"search": search, "page": page, "page_size": page_size}
        return await client.get("/stages/all/", params=params)

    @mcp.tool(tags={"stages"})
    async def authentik_stage_identification_get(stage_uuid: str) -> dict[str, Any]:
        """Ambil pengaturan satu stage identification (mis. source yang ditampilkan).

        Args:
            stage_uuid: UUID stage identification.

        Returns:
            Objek stage identification apa adanya dari API.

        Raises:
            AuthentikAPIError: 404 bila stage tidak ditemukan.
        """
        return await client.get(f"/stages/identification/{stage_uuid}/")

    @mcp.tool(tags={"stages"})
    async def authentik_stage_authenticator_validate_get(stage_uuid: str) -> dict[str, Any]:
        """Ambil pengaturan satu stage authenticator validate (validasi MFA).

        Args:
            stage_uuid: UUID stage authenticator validate.

        Returns:
            Objek stage apa adanya dari API (mis. kelas device dan ``not_configured_action``).

        Raises:
            AuthentikAPIError: 404 bila stage tidak ditemukan.
        """
        return await client.get(f"/stages/authenticator/validate/{stage_uuid}/")
