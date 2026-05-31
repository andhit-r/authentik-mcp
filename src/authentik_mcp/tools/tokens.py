"""Tool MCP untuk mengelola Token Authentik (endpoint ``/core/tokens/``).

Mendaftarkan tool: list, get, create, revoke.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import AuthentikClient


def register(mcp: FastMCP, client: AuthentikClient) -> None:
    """Daftarkan seluruh tool domain Token ke server MCP.

    Args:
        mcp: Instance FastMCP.
        client: Klien Authentik bersama.
    """

    @mcp.tool(tags={"tokens"})
    async def authentik_token_list(
        search: str | None = None,
        user_id: int | None = None,
        intent: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Daftar token dengan filter dan paginasi.

        Args:
            search: Kata kunci pencarian (identifier/deskripsi).
            user_id: pk user pemilik token untuk memfilter.
            intent: Maksud token: ``api``, ``app_password``, ``recovery``, dll.
            page: Nomor halaman.
            page_size: Jumlah item per halaman.

        Returns:
            Objek paginasi berisi ``results`` (daftar token) dan ``pagination``.
            Catatan: nilai rahasia (key) token tidak dikembalikan saat list.

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        params = {
            "search": search,
            "user": user_id,
            "intent": intent,
            "page": page,
            "page_size": page_size,
        }
        return await client.get("/core/tokens/", params=params)

    @mcp.tool(tags={"tokens"})
    async def authentik_token_get(identifier: str) -> dict[str, Any]:
        """Ambil metadata satu token berdasarkan identifier.

        Args:
            identifier: Identifier unik token.

        Returns:
            Objek token (metadata; bukan nilai rahasianya).

        Raises:
            AuthentikAPIError: 404 bila token tidak ditemukan.
        """
        return await client.get(f"/core/tokens/{identifier}/")

    @mcp.tool(tags={"tokens"})
    async def authentik_token_create(
        identifier: str,
        user_id: int,
        intent: str = "api",
        description: str | None = None,
        expiring: bool = True,
    ) -> dict[str, Any]:
        """Buat token baru milik seorang user.

        Args:
            identifier: Identifier unik untuk token.
            user_id: pk user pemilik token.
            intent: Maksud token (``api`` default, atau ``app_password`` dll).
            description: Deskripsi token (opsional).
            expiring: Apakah token memiliki masa berlaku (kedaluwarsa).

        Returns:
            Objek token yang baru dibuat.

        Raises:
            AuthentikAPIError: 422 bila validasi gagal (mis. identifier duplikat).
        """
        payload: dict[str, Any] = {
            "identifier": identifier,
            "user": user_id,
            "intent": intent,
            "expiring": expiring,
        }
        if description is not None:
            payload["description"] = description
        return await client.post("/core/tokens/", json=payload)

    @mcp.tool(tags={"tokens"})
    async def authentik_token_revoke(identifier: str) -> dict[str, str]:
        """Cabut (hapus) sebuah token sehingga tidak lagi valid.

        Args:
            identifier: Identifier token yang dicabut.

        Returns:
            Konfirmasi pencabutan.

        Raises:
            AuthentikAPIError: 404 bila token tidak ditemukan.
        """
        await client.delete(f"/core/tokens/{identifier}/")
        return {"status": "revoked", "identifier": identifier}
