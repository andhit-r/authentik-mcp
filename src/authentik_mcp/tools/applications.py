"""Tool MCP untuk mengelola Application Authentik (endpoint ``/core/applications/``).

Mendaftarkan tool: list, get, create, update, delete.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import AuthentikClient


def register(mcp: FastMCP, client: AuthentikClient) -> None:
    """Daftarkan seluruh tool domain Application ke server MCP.

    Args:
        mcp: Instance FastMCP.
        client: Klien Authentik bersama.
    """

    @mcp.tool(tags={"applications"})
    async def authentik_application_list(
        search: str | None = None,
        name: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Daftar application dengan filter dan paginasi.

        Args:
            search: Kata kunci pencarian (nama/slug).
            name: Filter persis berdasarkan nama.
            page: Nomor halaman.
            page_size: Jumlah item per halaman.

        Returns:
            Objek paginasi berisi ``results`` (daftar application) dan ``pagination``.

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        params = {
            "search": search,
            "name": name,
            "page": page,
            "page_size": page_size,
        }
        return await client.get("/core/applications/", params=params)

    @mcp.tool(tags={"applications"})
    async def authentik_application_get(slug: str) -> dict[str, Any]:
        """Ambil detail satu application berdasarkan slug.

        Args:
            slug: Slug unik application.

        Returns:
            Objek application lengkap.

        Raises:
            AuthentikAPIError: 404 bila application tidak ditemukan.
        """
        return await client.get(f"/core/applications/{slug}/")

    @mcp.tool(tags={"applications"})
    async def authentik_application_create(
        name: str,
        slug: str,
        provider: int | None = None,
        meta_description: str | None = None,
        meta_launch_url: str | None = None,
        group: str | None = None,
        policy_engine_mode: str = "any",
    ) -> dict[str, Any]:
        """Buat application baru.

        Args:
            name: Nama application.
            slug: Slug unik (dipakai pada URL).
            provider: pk provider yang ditautkan (opsional).
            meta_description: Deskripsi yang tampil di halaman aplikasi pengguna.
            meta_launch_url: URL peluncuran aplikasi.
            group: Nama grup tampilan (kategori) untuk aplikasi.
            policy_engine_mode: Mode evaluasi kebijakan: ``any`` atau ``all``.

        Returns:
            Objek application yang baru dibuat.

        Raises:
            AuthentikAPIError: 422 bila validasi gagal (mis. slug sudah dipakai).
        """
        payload: dict[str, Any] = {
            "name": name,
            "slug": slug,
            "policy_engine_mode": policy_engine_mode,
        }
        for key, value in {
            "provider": provider,
            "meta_description": meta_description,
            "meta_launch_url": meta_launch_url,
            "group": group,
        }.items():
            if value is not None:
                payload[key] = value
        return await client.post("/core/applications/", json=payload)

    @mcp.tool(tags={"applications"})
    async def authentik_application_update(
        slug: str,
        name: str | None = None,
        provider: int | None = None,
        meta_description: str | None = None,
        meta_launch_url: str | None = None,
        group: str | None = None,
        policy_engine_mode: str | None = None,
    ) -> dict[str, Any]:
        """Perbarui sebagian field application (PATCH). Hanya field non-None dikirim.

        Args:
            slug: Slug application yang akan diperbarui.
            name: Nama baru.
            provider: pk provider baru.
            meta_description: Deskripsi baru.
            meta_launch_url: URL peluncuran baru.
            group: Grup tampilan baru.
            policy_engine_mode: Mode kebijakan baru (``any``/``all``).

        Returns:
            Objek application setelah diperbarui.

        Raises:
            AuthentikAPIError: 404 bila tidak ditemukan, 422 bila validasi gagal.
        """
        payload: dict[str, Any] = {}
        for key, value in {
            "name": name,
            "provider": provider,
            "meta_description": meta_description,
            "meta_launch_url": meta_launch_url,
            "group": group,
            "policy_engine_mode": policy_engine_mode,
        }.items():
            if value is not None:
                payload[key] = value
        if not payload:
            raise ValueError("Tidak ada field yang diberikan untuk diperbarui.")
        return await client.patch(f"/core/applications/{slug}/", json=payload)

    @mcp.tool(tags={"applications"})
    async def authentik_application_delete(slug: str) -> dict[str, str]:
        """Hapus application secara permanen.

        Args:
            slug: Slug application.

        Returns:
            Konfirmasi penghapusan.

        Raises:
            AuthentikAPIError: 404 bila application tidak ditemukan.
        """
        await client.delete(f"/core/applications/{slug}/")
        return {"status": "deleted", "slug": slug}
