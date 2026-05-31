"""Tool MCP untuk mengelola Group Authentik (endpoint ``/core/groups/``).

Mendaftarkan tool: list, get, create, update, delete, tambah/hapus member.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import AuthentikClient


def register(mcp: FastMCP, client: AuthentikClient) -> None:
    """Daftarkan seluruh tool domain Group ke server MCP.

    Args:
        mcp: Instance FastMCP.
        client: Klien Authentik bersama.
    """

    @mcp.tool(tags={"groups"})
    async def authentik_group_list(
        search: str | None = None,
        name: str | None = None,
        is_superuser: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Daftar grup Authentik dengan filter dan paginasi.

        Args:
            search: Kata kunci pencarian nama grup.
            name: Filter persis berdasarkan nama grup.
            is_superuser: Filter grup superuser (True/False).
            page: Nomor halaman.
            page_size: Jumlah item per halaman.

        Returns:
            Objek paginasi berisi ``results`` (daftar grup) dan ``pagination``.

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        params = {
            "search": search,
            "name": name,
            "is_superuser": is_superuser,
            "page": page,
            "page_size": page_size,
        }
        return await client.get("/core/groups/", params=params)

    @mcp.tool(tags={"groups"})
    async def authentik_group_get(group_uuid: str) -> dict[str, Any]:
        """Ambil detail satu grup berdasarkan UUID.

        Args:
            group_uuid: UUID (pk) grup.

        Returns:
            Objek grup lengkap termasuk daftar anggota.

        Raises:
            AuthentikAPIError: 404 bila grup tidak ditemukan.
        """
        return await client.get(f"/core/groups/{group_uuid}/")

    @mcp.tool(tags={"groups"})
    async def authentik_group_create(
        name: str,
        is_superuser: bool = False,
        parent: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Buat grup baru.

        Args:
            name: Nama grup (harus unik).
            is_superuser: Apakah anggota grup memiliki hak superuser.
            parent: UUID grup induk (untuk hierarki). Opsional.
            attributes: Atribut kustom grup. Opsional.

        Returns:
            Objek grup yang baru dibuat (termasuk ``pk``).

        Raises:
            AuthentikAPIError: 422 bila validasi gagal (mis. nama sudah ada).
        """
        payload: dict[str, Any] = {"name": name, "is_superuser": is_superuser}
        if parent is not None:
            payload["parent"] = parent
        if attributes is not None:
            payload["attributes"] = attributes
        return await client.post("/core/groups/", json=payload)

    @mcp.tool(tags={"groups"})
    async def authentik_group_update(
        group_uuid: str,
        name: str | None = None,
        is_superuser: bool | None = None,
        parent: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Perbarui sebagian field grup (PATCH). Hanya field non-None yang dikirim.

        Args:
            group_uuid: UUID grup.
            name: Nama baru.
            is_superuser: Status superuser baru.
            parent: UUID grup induk baru.
            attributes: Atribut kustom baru.

        Returns:
            Objek grup setelah diperbarui.

        Raises:
            AuthentikAPIError: 404 bila grup tidak ditemukan, 422 bila validasi gagal.
        """
        payload: dict[str, Any] = {}
        for key, value in {
            "name": name,
            "is_superuser": is_superuser,
            "parent": parent,
            "attributes": attributes,
        }.items():
            if value is not None:
                payload[key] = value
        if not payload:
            raise ValueError("Tidak ada field yang diberikan untuk diperbarui.")
        return await client.patch(f"/core/groups/{group_uuid}/", json=payload)

    @mcp.tool(tags={"groups"})
    async def authentik_group_delete(group_uuid: str) -> dict[str, str]:
        """Hapus grup secara permanen.

        Args:
            group_uuid: UUID grup.

        Returns:
            Konfirmasi penghapusan.

        Raises:
            AuthentikAPIError: 404 bila grup tidak ditemukan.
        """
        await client.delete(f"/core/groups/{group_uuid}/")
        return {"status": "deleted", "group_uuid": group_uuid}

    @mcp.tool(tags={"groups"})
    async def authentik_group_add_member(group_uuid: str, user_id: int) -> dict[str, str]:
        """Tambahkan seorang user sebagai anggota grup.

        Args:
            group_uuid: UUID grup.
            user_id: pk numerik user yang ditambahkan.

        Returns:
            Konfirmasi keberhasilan.

        Raises:
            AuthentikAPIError: 404 bila grup/user tidak ditemukan.
        """
        await client.post(f"/core/groups/{group_uuid}/add_user/", json={"pk": user_id})
        return {"status": "member_added", "group_uuid": group_uuid, "user_id": str(user_id)}

    @mcp.tool(tags={"groups"})
    async def authentik_group_remove_member(group_uuid: str, user_id: int) -> dict[str, str]:
        """Keluarkan seorang user dari keanggotaan grup.

        Args:
            group_uuid: UUID grup.
            user_id: pk numerik user yang dikeluarkan.

        Returns:
            Konfirmasi keberhasilan.

        Raises:
            AuthentikAPIError: 404 bila grup/user tidak ditemukan.
        """
        await client.post(f"/core/groups/{group_uuid}/remove_user/", json={"pk": user_id})
        return {
            "status": "member_removed",
            "group_uuid": group_uuid,
            "user_id": str(user_id),
        }
