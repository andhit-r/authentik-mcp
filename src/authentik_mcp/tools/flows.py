"""Tool MCP untuk mengelola Flow Authentik (endpoint ``/flows/``).

Mendaftarkan tool: list, get, create, update, delete, dan execute (memulai eksekusi flow).
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import AuthentikClient


def register(mcp: FastMCP, client: AuthentikClient) -> None:
    """Daftarkan seluruh tool domain Flow ke server MCP.

    Args:
        mcp: Instance FastMCP.
        client: Klien Authentik bersama.
    """

    @mcp.tool(tags={"flows"})
    async def authentik_flow_list(
        search: str | None = None,
        designation: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Daftar flow dengan filter dan paginasi.

        Args:
            search: Kata kunci pencarian (nama/slug/title).
            designation: Filter berdasarkan peruntukan flow (mis.
                ``authentication``, ``authorization``, ``enrollment``,
                ``recovery``, ``invalidation``).
            page: Nomor halaman.
            page_size: Jumlah item per halaman.

        Returns:
            Objek paginasi berisi ``results`` (daftar flow) dan ``pagination``.

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        params = {
            "search": search,
            "designation": designation,
            "page": page,
            "page_size": page_size,
        }
        return await client.get("/flows/instances/", params=params)

    @mcp.tool(tags={"flows"})
    async def authentik_flow_get(slug: str) -> dict[str, Any]:
        """Ambil detail satu flow berdasarkan slug.

        Args:
            slug: Slug unik flow.

        Returns:
            Objek flow lengkap.

        Raises:
            AuthentikAPIError: 404 bila flow tidak ditemukan.
        """
        return await client.get(f"/flows/instances/{slug}/")

    @mcp.tool(tags={"flows"})
    async def authentik_flow_execute(slug: str) -> dict[str, Any]:
        """Mulai eksekusi sebuah flow dan kembalikan challenge tahap pertama.

        Memanggil endpoint executor Authentik (``/flows/executor/{slug}/``) yang
        mengembalikan ``challenge`` untuk tahap (stage) pertama dari flow.

        Args:
            slug: Slug flow yang dieksekusi.

        Returns:
            Objek challenge tahap pertama (mis. komponen form yang harus diisi).

        Raises:
            AuthentikAPIError: 404 bila flow tidak ditemukan, atau error lain.
        """
        # query=- diperlukan oleh executor Authentik sebagai parameter awal.
        return await client.get(f"/flows/executor/{slug}/", params={"query": ""})

    @mcp.tool(tags={"flows"})
    async def authentik_flow_create(
        name: str,
        slug: str,
        title: str,
        designation: str,
        policy_engine_mode: str = "any",
        authentication: str = "none",
        denied_action: str = "message_continue",
        layout: str = "stacked",
        compatibility_mode: bool = False,
    ) -> dict[str, Any]:
        """Buat flow baru.

        Args:
            name: Nama internal flow.
            slug: Slug unik yang dipakai pada URL (mis. ``my-auth-flow``).
            title: Judul yang ditampilkan kepada pengguna saat flow berjalan.
            designation: Peruntukan flow. Nilai valid: ``authentication``,
                ``authorization``, ``enrollment``, ``recovery``, ``invalidation``,
                ``unenrollment``, ``configuration``.
            policy_engine_mode: Mode evaluasi kebijakan: ``any`` (default) atau
                ``all``.
            authentication: Persyaratan autentikasi untuk mengakses flow. Nilai
                valid: ``none``, ``require_authenticated``,
                ``require_unauthenticated``, ``require_superuser``. Default:
                ``none``.
            denied_action: Aksi saat kebijakan menolak akses: ``message_continue``
                (default), ``message``, atau ``continue``.
            layout: Tata letak UI flow: ``stacked`` (default), ``content_left``,
                ``content_right``, ``sidebar_left``, ``sidebar_right``.
            compatibility_mode: Aktifkan mode kompatibilitas browser lama.
                Default: ``False``.

        Returns:
            Objek flow yang baru dibuat.

        Raises:
            AuthentikAPIError: 422 bila validasi gagal (mis. slug sudah dipakai).
        """
        payload: dict[str, Any] = {
            "name": name,
            "slug": slug,
            "title": title,
            "designation": designation,
            "policy_engine_mode": policy_engine_mode,
            "authentication": authentication,
            "denied_action": denied_action,
            "layout": layout,
            "compatibility_mode": compatibility_mode,
        }
        return await client.post("/flows/instances/", json=payload)

    @mcp.tool(tags={"flows"})
    async def authentik_flow_update(
        slug: str,
        name: str | None = None,
        title: str | None = None,
        designation: str | None = None,
        policy_engine_mode: str | None = None,
        authentication: str | None = None,
        denied_action: str | None = None,
        layout: str | None = None,
        compatibility_mode: bool | None = None,
    ) -> dict[str, Any]:
        """Perbarui sebagian field flow (PATCH). Hanya field non-None dikirim.

        Args:
            slug: Slug flow yang akan diperbarui.
            name: Nama internal baru.
            title: Judul tampilan baru.
            designation: Peruntukan baru (``authentication``, ``authorization``,
                ``enrollment``, ``recovery``, ``invalidation``, ``unenrollment``,
                ``configuration``).
            policy_engine_mode: Mode kebijakan baru (``any``/``all``).
            authentication: Persyaratan autentikasi baru.
            denied_action: Aksi deny baru.
            layout: Tata letak baru.
            compatibility_mode: Status mode kompatibilitas baru.

        Returns:
            Objek flow setelah diperbarui.

        Raises:
            ValueError: Bila tidak ada field yang diberikan.
            AuthentikAPIError: 404 bila flow tidak ditemukan, 422 bila validasi
                gagal.
        """
        payload: dict[str, Any] = {}
        for key, value in {
            "name": name,
            "title": title,
            "designation": designation,
            "policy_engine_mode": policy_engine_mode,
            "authentication": authentication,
            "denied_action": denied_action,
            "layout": layout,
            "compatibility_mode": compatibility_mode,
        }.items():
            if value is not None:
                payload[key] = value
        if not payload:
            raise ValueError("Tidak ada field yang diberikan untuk diperbarui.")
        return await client.patch(f"/flows/instances/{slug}/", json=payload)

    @mcp.tool(tags={"flows"})
    async def authentik_flow_delete(slug: str) -> dict[str, str]:
        """Hapus flow secara permanen.

        Args:
            slug: Slug flow yang akan dihapus.

        Returns:
            Konfirmasi penghapusan berisi ``status`` dan ``slug``.

        Raises:
            AuthentikAPIError: 404 bila flow tidak ditemukan.
        """
        await client.delete(f"/flows/instances/{slug}/")
        return {"status": "deleted", "slug": slug}
