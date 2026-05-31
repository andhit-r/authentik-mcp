"""Tool MCP untuk mengelola User Authentik (endpoint ``/core/users/``).

Mendaftarkan tool: list, get, create, update, delete, set password,
activate/deactivate.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import AuthentikClient


def register(mcp: FastMCP, client: AuthentikClient) -> None:
    """Daftarkan seluruh tool domain User ke server MCP.

    Args:
        mcp: Instance FastMCP.
        client: Klien Authentik bersama.
    """

    @mcp.tool(tags={"users"})
    async def authentik_user_list(
        search: str | None = None,
        username: str | None = None,
        is_active: bool | None = None,
        group: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Daftar user Authentik dengan filter dan paginasi.

        Args:
            search: Kata kunci pencarian (mencocokkan username, nama, email).
            username: Filter persis berdasarkan username.
            is_active: Filter berdasarkan status aktif (True/False).
            group: UUID grup untuk memfilter anggotanya.
            page: Nomor halaman (mulai dari 1).
            page_size: Jumlah item per halaman.

        Returns:
            Objek paginasi Authentik berisi ``results`` (daftar user) dan
            ``pagination`` (metadata halaman).

        Raises:
            AuthentikAPIError: Bila request gagal (mis. 401 token tidak valid).
        """
        params = {
            "search": search,
            "username": username,
            "is_active": is_active,
            "groups_by_uuid": group,
            "page": page,
            "page_size": page_size,
        }
        return await client.get("/core/users/", params=params)

    @mcp.tool(tags={"users"})
    async def authentik_user_get(user_id: int) -> dict[str, Any]:
        """Ambil detail satu user berdasarkan ID (pk numerik).

        Args:
            user_id: Primary key (pk) numerik user.

        Returns:
            Objek user lengkap.

        Raises:
            AuthentikAPIError: 404 bila user tidak ditemukan.
        """
        return await client.get(f"/core/users/{user_id}/")

    @mcp.tool(tags={"users"})
    async def authentik_user_create(
        username: str,
        name: str,
        email: str | None = None,
        is_active: bool = True,
        groups: list[str] | None = None,
        attributes: dict[str, Any] | None = None,
        path: str = "users",
        user_type: str = "internal",
    ) -> dict[str, Any]:
        """Buat user baru.

        Args:
            username: Username unik.
            name: Nama tampilan user.
            email: Alamat email (opsional).
            is_active: Apakah user aktif setelah dibuat.
            groups: Daftar UUID grup yang langsung ditambahkan ke user.
            attributes: Atribut kustom (dict bebas) untuk user.
            path: Path direktori user di Authentik (default ``users``).
            user_type: Tipe user: ``internal``, ``external``, ``service_account``,
                atau ``internal_service_account``.

        Returns:
            Objek user yang baru dibuat (termasuk ``pk``).

        Raises:
            AuthentikAPIError: 422 bila validasi gagal (mis. username sudah ada).
        """
        payload: dict[str, Any] = {
            "username": username,
            "name": name,
            "is_active": is_active,
            "path": path,
            "type": user_type,
        }
        if email is not None:
            payload["email"] = email
        if groups is not None:
            payload["groups"] = groups
        if attributes is not None:
            payload["attributes"] = attributes
        return await client.post("/core/users/", json=payload)

    @mcp.tool(tags={"users"})
    async def authentik_user_update(
        user_id: int,
        username: str | None = None,
        name: str | None = None,
        email: str | None = None,
        is_active: bool | None = None,
        groups: list[str] | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Perbarui sebagian field user (PATCH). Hanya field non-None yang dikirim.

        Args:
            user_id: pk numerik user.
            username: Username baru.
            name: Nama tampilan baru.
            email: Email baru.
            is_active: Status aktif baru.
            groups: Daftar UUID grup baru (menggantikan keanggotaan lama).
            attributes: Atribut kustom baru.

        Returns:
            Objek user setelah diperbarui.

        Raises:
            AuthentikAPIError: 404 bila user tidak ditemukan, 422 bila validasi gagal.
        """
        payload: dict[str, Any] = {}
        for key, value in {
            "username": username,
            "name": name,
            "email": email,
            "is_active": is_active,
            "groups": groups,
            "attributes": attributes,
        }.items():
            if value is not None:
                payload[key] = value
        if not payload:
            raise ValueError("Tidak ada field yang diberikan untuk diperbarui.")
        return await client.patch(f"/core/users/{user_id}/", json=payload)

    @mcp.tool(tags={"users"})
    async def authentik_user_delete(user_id: int) -> dict[str, str]:
        """Hapus user secara permanen.

        Args:
            user_id: pk numerik user.

        Returns:
            Konfirmasi penghapusan.

        Raises:
            AuthentikAPIError: 404 bila user tidak ditemukan.
        """
        await client.delete(f"/core/users/{user_id}/")
        return {"status": "deleted", "user_id": str(user_id)}

    @mcp.tool(tags={"users"})
    async def authentik_user_set_password(user_id: int, password: str) -> dict[str, str]:
        """Set/ubah password user.

        Args:
            user_id: pk numerik user.
            password: Password baru (plaintext; Authentik yang melakukan hashing).

        Returns:
            Konfirmasi keberhasilan.

        Raises:
            AuthentikAPIError: 404 bila user tidak ditemukan, 422 bila password
                tidak memenuhi kebijakan.
        """
        await client.post(f"/core/users/{user_id}/set_password/", json={"password": password})
        return {"status": "password_set", "user_id": str(user_id)}

    @mcp.tool(tags={"users"})
    async def authentik_user_activate(user_id: int) -> dict[str, Any]:
        """Aktifkan user (set ``is_active=true``).

        Args:
            user_id: pk numerik user.

        Returns:
            Objek user setelah diaktifkan.

        Raises:
            AuthentikAPIError: 404 bila user tidak ditemukan.
        """
        return await client.patch(f"/core/users/{user_id}/", json={"is_active": True})

    @mcp.tool(tags={"users"})
    async def authentik_user_deactivate(user_id: int) -> dict[str, Any]:
        """Nonaktifkan user (set ``is_active=false``).

        Args:
            user_id: pk numerik user.

        Returns:
            Objek user setelah dinonaktifkan.

        Raises:
            AuthentikAPIError: 404 bila user tidak ditemukan.
        """
        return await client.patch(f"/core/users/{user_id}/", json={"is_active": False})
