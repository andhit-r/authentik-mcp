"""Tool MCP untuk mengelola RBAC/Roles Authentik.

Endpoint: ``/core/roles/`` (CRUD role) dan ``/rbac/permissions/``
(katalog permission + assignment ke role/user).

Mendaftarkan tool:
- Role CRUD + daftar objek yang memakai role (6 tool)
- Katalog permission sistem (1 tool)
- Permission yang di-assign ke role: list, assign, unassign (3 tool)
- Permission yang di-assign langsung ke user: list, assign, unassign (3 tool)
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import AuthentikClient


def register(mcp: FastMCP, client: AuthentikClient) -> None:
    """Daftarkan seluruh tool domain RBAC/Roles ke server MCP.

    Args:
        mcp: Instance FastMCP.
        client: Klien Authentik bersama.
    """

    # ── Role CRUD ──────────────────────────────────────────────────────────

    @mcp.tool(tags={"roles"})
    async def authentik_role_list(
        search: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Daftar role Authentik dengan filter dan paginasi.

        Args:
            search: Kata kunci pencarian nama role.
            page: Nomor halaman.
            page_size: Jumlah item per halaman.

        Returns:
            Objek paginasi berisi ``results`` (daftar role) dan ``pagination``.

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        params: dict[str, Any] = {
            "search": search,
            "page": page,
            "page_size": page_size,
        }
        return await client.get("/core/roles/", params=params)

    @mcp.tool(tags={"roles"})
    async def authentik_role_get(role_uuid: str) -> dict[str, Any]:
        """Ambil detail satu role berdasarkan UUID.

        Args:
            role_uuid: UUID (pk) role.

        Returns:
            Objek role.

        Raises:
            AuthentikAPIError: 404 bila role tidak ditemukan.
        """
        return await client.get(f"/core/roles/{role_uuid}/")

    @mcp.tool(tags={"roles"})
    async def authentik_role_create(name: str) -> dict[str, Any]:
        """Buat role baru.

        Args:
            name: Nama role (harus unik).

        Returns:
            Objek role yang baru dibuat (termasuk ``pk``).

        Raises:
            AuthentikAPIError: 422 bila validasi gagal (mis. nama sudah ada).
        """
        return await client.post("/core/roles/", json={"name": name})

    @mcp.tool(tags={"roles"})
    async def authentik_role_update(role_uuid: str, name: str) -> dict[str, Any]:
        """Perbarui nama role.

        Args:
            role_uuid: UUID role.
            name: Nama baru role.

        Returns:
            Objek role setelah diperbarui.

        Raises:
            AuthentikAPIError: 404 bila role tidak ditemukan, 422 bila validasi gagal.
        """
        return await client.patch(f"/core/roles/{role_uuid}/", json={"name": name})

    @mcp.tool(tags={"roles"})
    async def authentik_role_delete(role_uuid: str) -> dict[str, str]:
        """Hapus role secara permanen.

        Args:
            role_uuid: UUID role.

        Returns:
            Konfirmasi penghapusan.

        Raises:
            AuthentikAPIError: 404 bila role tidak ditemukan.
        """
        await client.delete(f"/core/roles/{role_uuid}/")
        return {"status": "deleted", "role_uuid": role_uuid}

    @mcp.tool(tags={"roles"})
    async def authentik_role_used_by(role_uuid: str) -> list[dict[str, Any]]:
        """Daftar objek (user, group, dll) yang menggunakan role ini.

        Args:
            role_uuid: UUID role.

        Returns:
            Daftar objek yang mereferensikan role ini.

        Raises:
            AuthentikAPIError: 404 bila role tidak ditemukan.
        """
        return await client.get(f"/core/roles/{role_uuid}/used_by/")

    # ── Katalog permission sistem ───────────────────────────────────────────

    @mcp.tool(tags={"roles"})
    async def authentik_rbac_permission_list(
        codename: str | None = None,
        model: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Daftar seluruh permission yang tersedia di sistem Authentik.

        Args:
            codename: Filter berdasarkan codename (mis. ``view_application``).
            model: Filter berdasarkan nama model (mis. ``authentik_core.application``).
            page: Nomor halaman.
            page_size: Jumlah item per halaman.

        Returns:
            Objek paginasi berisi daftar permission.

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        params: dict[str, Any] = {
            "codename": codename,
            "model": model,
            "page": page,
            "page_size": page_size,
        }
        return await client.get("/rbac/permissions/", params=params)

    # ── Permission yang di-assign ke Role ──────────────────────────────────

    @mcp.tool(tags={"roles"})
    async def authentik_rbac_role_permission_list(
        role_uuid: str | None = None,
        model: str | None = None,
        object_pk: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Daftar permission yang di-assign ke sebuah role.

        Args:
            role_uuid: UUID role untuk filter. Opsional — kosongkan untuk semua role.
            model: Filter berdasarkan nama model.
            object_pk: Filter berdasarkan pk objek (untuk object-level permission).
            page: Nomor halaman.
            page_size: Jumlah item per halaman.

        Returns:
            Objek paginasi berisi daftar role permission assignment.

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        params: dict[str, Any] = {
            "role": role_uuid,
            "model": model,
            "object_pk": object_pk,
            "page": page,
            "page_size": page_size,
        }
        return await client.get("/rbac/permissions/assigned_by_roles/", params=params)

    @mcp.tool(tags={"roles"})
    async def authentik_rbac_role_assign_permission(
        role_uuid: str,
        permissions: list[str],
        model: str | None = None,
        object_pk: str | None = None,
    ) -> dict[str, Any]:
        """Tambahkan satu atau beberapa permission ke sebuah role.

        Untuk global permission (tidak terikat objek tertentu), kirim
        ``role_uuid`` dan ``permissions`` saja. Untuk object-level permission,
        sertakan juga ``model`` dan ``object_pk``.

        Args:
            role_uuid: UUID role tujuan.
            permissions: Daftar codename permission
                (mis. ``["view_application", "add_application"]``).
            model: Nama model untuk object-level permission
                (mis. ``authentik_core.application``). Opsional.
            object_pk: PK objek untuk object-level permission. Opsional.

        Returns:
            Konfirmasi keberhasilan dari API.

        Raises:
            AuthentikAPIError: Bila request gagal atau permission tidak dikenal.
        """
        payload: dict[str, Any] = {"role": role_uuid, "permissions": permissions}
        if model is not None:
            payload["model"] = model
        if object_pk is not None:
            payload["object_pk"] = object_pk
        return await client.post("/rbac/permissions/assigned_by_roles/assign/", json=payload)

    @mcp.tool(tags={"roles"})
    async def authentik_rbac_role_unassign_permission(permission_id: int) -> dict[str, str]:
        """Cabut permission dari role berdasarkan ID assignment.

        Gunakan ``authentik_rbac_role_permission_list`` terlebih dahulu
        untuk mendapatkan ``id`` assignment yang ingin dicabut.

        Args:
            permission_id: ID numerik dari assignment permission (field ``id``).

        Returns:
            Konfirmasi pencabutan.

        Raises:
            AuthentikAPIError: 404 bila assignment tidak ditemukan.
        """
        await client.delete(f"/rbac/permissions/assigned_by_roles/{permission_id}/")
        return {"status": "unassigned", "permission_id": str(permission_id)}

    # ── Permission yang di-assign langsung ke User ─────────────────────────

    @mcp.tool(tags={"roles"})
    async def authentik_rbac_user_permission_list(
        user_id: int | None = None,
        model: str | None = None,
        object_pk: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Daftar permission yang di-assign langsung ke sebuah user.

        Ini hanya mencakup permission yang di-assign secara eksplisit per user,
        bukan yang diwarisi melalui role atau group.

        Args:
            user_id: pk numerik user untuk filter. Opsional.
            model: Filter berdasarkan nama model.
            object_pk: Filter berdasarkan pk objek (untuk object-level permission).
            page: Nomor halaman.
            page_size: Jumlah item per halaman.

        Returns:
            Objek paginasi berisi daftar user permission assignment.

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        params: dict[str, Any] = {
            "user": user_id,
            "model": model,
            "object_pk": object_pk,
            "page": page,
            "page_size": page_size,
        }
        return await client.get("/rbac/permissions/assigned_by_users/", params=params)

    @mcp.tool(tags={"roles"})
    async def authentik_rbac_user_assign_permission(
        user_id: int,
        permissions: list[str],
        model: str | None = None,
        object_pk: str | None = None,
    ) -> dict[str, Any]:
        """Tambahkan satu atau beberapa permission langsung ke sebuah user.

        Untuk global permission, kirim ``user_id`` dan ``permissions`` saja.
        Untuk object-level permission, sertakan juga ``model`` dan ``object_pk``.

        Args:
            user_id: pk numerik user tujuan.
            permissions: Daftar codename permission.
            model: Nama model untuk object-level permission. Opsional.
            object_pk: PK objek untuk object-level permission. Opsional.

        Returns:
            Konfirmasi keberhasilan dari API.

        Raises:
            AuthentikAPIError: Bila request gagal atau permission tidak dikenal.
        """
        payload: dict[str, Any] = {"user": user_id, "permissions": permissions}
        if model is not None:
            payload["model"] = model
        if object_pk is not None:
            payload["object_pk"] = object_pk
        return await client.post("/rbac/permissions/assigned_by_users/assign/", json=payload)

    @mcp.tool(tags={"roles"})
    async def authentik_rbac_user_unassign_permission(permission_id: int) -> dict[str, str]:
        """Cabut permission dari user berdasarkan ID assignment.

        Gunakan ``authentik_rbac_user_permission_list`` terlebih dahulu
        untuk mendapatkan ``id`` assignment yang ingin dicabut.

        Args:
            permission_id: ID numerik dari assignment permission (field ``id``).

        Returns:
            Konfirmasi pencabutan.

        Raises:
            AuthentikAPIError: 404 bila assignment tidak ditemukan.
        """
        await client.delete(f"/rbac/permissions/assigned_by_users/{permission_id}/")
        return {"status": "unassigned", "permission_id": str(permission_id)}
