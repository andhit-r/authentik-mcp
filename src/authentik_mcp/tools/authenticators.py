"""Tool MCP (baca-saja) untuk device MFA (endpoint ``/authenticators/admin/``).

Mendaftarkan tool ``authentik_authenticator_admin_list``. Hanya metadata device
yang dikembalikan API; tidak ada tool tulis.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import AuthentikClient


def register(mcp: FastMCP, client: AuthentikClient) -> None:
    """Daftarkan tool baca-saja domain device MFA ke server MCP.

    Args:
        mcp: Instance FastMCP.
        client: Klien Authentik bersama.
    """

    @mcp.tool(tags={"authenticators"})
    async def authentik_authenticator_admin_list(user: int) -> Any:
        """Daftar device MFA milik seorang user (metadata saja).

        Args:
            user: ID numerik (pk) user.

        Returns:
            Daftar device MFA apa adanya dari API.

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        return await client.get("/authenticators/admin/all/", params={"user": user})
