"""Tool MCP untuk membaca Events/Logs Authentik (endpoint ``/events/events/``).

Mendaftarkan tool: list (dengan filter), get, serta filter cepat berdasarkan
action atau user.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import AuthentikClient


def register(mcp: FastMCP, client: AuthentikClient) -> None:
    """Daftarkan seluruh tool domain Events ke server MCP.

    Args:
        mcp: Instance FastMCP.
        client: Klien Authentik bersama.
    """

    @mcp.tool(tags={"events"})
    async def authentik_event_list(
        action: str | None = None,
        username: str | None = None,
        client_ip: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Daftar event/log audit Authentik dengan filter dan paginasi.

        Args:
            action: Filter berdasarkan jenis action (mis. ``login``,
                ``login_failed``, ``user_write``, ``model_created``).
            username: Filter berdasarkan username pelaku event.
            client_ip: Filter berdasarkan alamat IP klien.
            search: Kata kunci pencarian bebas.
            page: Nomor halaman.
            page_size: Jumlah item per halaman.

        Returns:
            Objek paginasi berisi ``results`` (daftar event) dan ``pagination``.

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        params = {
            "action": action,
            "username": username,
            "client_ip": client_ip,
            "search": search,
            "page": page,
            "page_size": page_size,
        }
        return await client.get("/events/events/", params=params)

    @mcp.tool(tags={"events"})
    async def authentik_event_get(event_uuid: str) -> dict[str, Any]:
        """Ambil detail satu event berdasarkan UUID.

        Args:
            event_uuid: UUID (pk) event.

        Returns:
            Objek event lengkap (termasuk context dan metadata).

        Raises:
            AuthentikAPIError: 404 bila event tidak ditemukan.
        """
        return await client.get(f"/events/events/{event_uuid}/")

    @mcp.tool(tags={"events"})
    async def authentik_event_filter_by_action(
        action: str, page: int = 1, page_size: int = 50
    ) -> dict[str, Any]:
        """Filter event berdasarkan satu jenis action (helper ringkas).

        Args:
            action: Jenis action yang dicari (mis. ``login_failed``).
            page: Nomor halaman.
            page_size: Jumlah item per halaman.

        Returns:
            Objek paginasi event yang cocok.

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        params = {"action": action, "page": page, "page_size": page_size}
        return await client.get("/events/events/", params=params)

    @mcp.tool(tags={"events"})
    async def authentik_event_filter_by_user(
        username: str, page: int = 1, page_size: int = 50
    ) -> dict[str, Any]:
        """Filter event berdasarkan username pelaku (helper ringkas).

        Args:
            username: Username pelaku event.
            page: Nomor halaman.
            page_size: Jumlah item per halaman.

        Returns:
            Objek paginasi event yang cocok.

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        params = {"username": username, "page": page, "page_size": page_size}
        return await client.get("/events/events/", params=params)
