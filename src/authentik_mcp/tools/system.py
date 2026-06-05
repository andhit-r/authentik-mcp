"""Tool MCP untuk informasi & konfigurasi sistem Authentik (endpoint ``/admin/``).

Mendaftarkan tool baca-only untuk versi, info sistem, daftar app & model, serta
tool baca/ubah pengaturan global (``/admin/settings/``) dan riwayat versi.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import AuthentikClient


def register(mcp: FastMCP, client: AuthentikClient) -> None:
    """Daftarkan seluruh tool domain System (admin) ke server MCP.

    Args:
        mcp: Instance FastMCP.
        client: Klien Authentik bersama.
    """

    @mcp.tool(tags={"system"})
    async def authentik_system_info() -> dict[str, Any]:
        """Ambil informasi runtime sistem Authentik.

        Returns:
            Objek berisi detail HTTP, Python, platform, runtime, dan konfigurasi
            server yang sedang berjalan.

        Raises:
            AuthentikAPIError: Bila request gagal (mis. 403 bukan superuser).
        """
        return await client.get("/admin/system/")

    @mcp.tool(tags={"system"})
    async def authentik_system_version() -> dict[str, Any]:
        """Ambil informasi versi Authentik (terpasang vs terbaru).

        Returns:
            Objek berisi ``version_current``, ``version_latest``, dan flag
            ``outdated``.

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        return await client.get("/admin/version/")

    @mcp.tool(tags={"system"})
    async def authentik_system_apps() -> list[dict[str, Any]]:
        """Daftar aplikasi Django yang terpasang di instance Authentik.

        Returns:
            Daftar objek app (``name``, ``label``).

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        return await client.get("/admin/apps/")

    @mcp.tool(tags={"system"})
    async def authentik_system_models() -> list[dict[str, Any]]:
        """Daftar model Django yang tersedia (berguna untuk RBAC/permission).

        Returns:
            Daftar objek model (``name``, ``label``).

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        return await client.get("/admin/models/")

    @mcp.tool(tags={"system"})
    async def authentik_system_settings_get() -> dict[str, Any]:
        """Ambil pengaturan global instance Authentik.

        Returns:
            Objek pengaturan global (avatars, retensi event, batas reputasi,
            footer links, durasi token default, paginasi, ``flags``, dll).

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        return await client.get("/admin/settings/")

    @mcp.tool(tags={"system"})
    async def authentik_system_settings_update(settings: dict[str, Any]) -> dict[str, Any]:
        """Perbarui sebagian pengaturan global instance (PATCH).

        Args:
            settings: Dict berisi field pengaturan yang ingin diubah, mis.
                ``{"event_retention": "days=60"}`` atau
                ``{"avatars": "gravatar,initials"}``.

        Returns:
            Objek pengaturan global setelah diperbarui.

        Raises:
            ValueError: Bila ``settings`` kosong.
            AuthentikAPIError: 422 bila nilai pengaturan tidak valid.
        """
        if not settings:
            raise ValueError("Parameter 'settings' tidak boleh kosong.")
        return await client.patch("/admin/settings/", json=settings)

    @mcp.tool(tags={"system"})
    async def authentik_system_version_history(
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Daftar riwayat versi Authentik yang pernah terpasang.

        Args:
            page: Nomor halaman.
            page_size: Jumlah item per halaman.

        Returns:
            Objek paginasi berisi ``results`` (riwayat versi).

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        params = {"page": page, "page_size": page_size}
        return await client.get("/admin/version/history/", params=params)
