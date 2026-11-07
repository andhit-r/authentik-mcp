"""Tool MCP untuk Stage Authentik (endpoint ``/stages/``).

Tool baca: ``authentik_stage_list``, ``authentik_stage_identification_get``,
``authentik_stage_authenticator_validate_get``. Tool tulis:
``authentik_stage_identification_update``.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import AuthentikClient


def register(mcp: FastMCP, client: AuthentikClient) -> None:
    """Daftarkan tool domain Stage (baca dan tulis) ke server MCP.

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

    @mcp.tool(tags={"stages"})
    async def authentik_stage_identification_update(
        stage_uuid: str,
        sources: list[str] | None = None,
        show_source_labels: bool | None = None,
    ) -> dict[str, Any]:
        """Perbarui stage identification (PATCH): daftar source dan label source.

        PERINGATAN: ``sources`` MENGGANTIKAN seluruh daftar source yang ada, bukan
        menambah. Baca daftar lama lebih dulu lewat
        ``authentik_stage_identification_get`` lalu kirim daftar lengkap yang
        diinginkan, atau source lain akan terlepas dari stage.

        Args:
            stage_uuid: UUID stage identification.
            sources: UUID source yang ditampilkan (menggantikan daftar lama);
                ``None`` berarti tidak diubah.
            show_source_labels: Tampilkan label source; ``None`` berarti tidak diubah.

        Returns:
            Objek stage identification setelah diperbarui.

        Raises:
            ValueError: Bila kedua argumen ``None``; API tidak dipanggil.
            AuthentikAPIError: 404 bila stage tidak ada, 422 bila validasi gagal.
        """
        payload: dict[str, Any] = {}
        if sources is not None:
            payload["sources"] = sources
        if show_source_labels is not None:
            payload["show_source_labels"] = show_source_labels
        if not payload:
            raise ValueError("Tidak ada field yang diberikan untuk diperbarui.")
        return await client.patch(f"/stages/identification/{stage_uuid}/", json=payload)
