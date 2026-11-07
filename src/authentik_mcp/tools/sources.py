"""Tool MCP untuk Source Authentik: daftar/baca source OAuth dan tulis source OAuth.

Tool baca: ``authentik_source_list``, ``authentik_source_oauth_list``,
``authentik_source_oauth_get``, ``authentik_source_connection_list``. Tool tulis:
``authentik_source_oauth_create``, ``authentik_source_oauth_update``,
``authentik_source_oauth_delete``. Kunci ``consumer_secret`` selalu dibuang dari
keluaran dan disamarkan dari pesan error.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import AuthentikAPIError, AuthentikClient

# Kunci rahasia yang tidak boleh sampai ke client MCP.
_SECRET_KEYS = frozenset({"consumer_secret"})


def _strip_secrets(data: Any) -> Any:
    """Buang kunci rahasia secara rekursif dari balasan API.

    Args:
        data: Balasan API (dict, list, atau nilai skalar).

    Returns:
        Salinan ``data`` tanpa kunci ``consumer_secret`` di level mana pun.
    """
    if isinstance(data, dict):
        return {k: _strip_secrets(v) for k, v in data.items() if k not in _SECRET_KEYS}
    if isinstance(data, list):
        return [_strip_secrets(item) for item in data]
    return data


def _redact_error(exc: AuthentikAPIError, secret: str | None) -> AuthentikAPIError:
    """Samarkan nilai rahasia dari error API sebelum diteruskan ke client.

    Args:
        exc: Error asli dari ``AuthentikClient``.
        secret: Nilai ``consumer_secret`` yang dikirim (``None`` bila tidak ada).

    Returns:
        ``exc`` apa adanya bila tidak ada rahasia; bila ada, error baru yang
        pesan dan ``detail``-nya sudah tidak memuat nilai rahasia.
    """
    if not secret:
        return exc
    detail = exc.detail
    if detail is not None:
        detail = str(detail).replace(secret, "***")
    return AuthentikAPIError(
        str(exc).replace(secret, "***"),
        status_code=exc.status_code,
        detail=detail,
        method=exc.method,
        path=exc.path,
    )


def _source_payload(**fields: Any) -> dict[str, Any]:
    """Susun payload source OAuth dengan membuang argumen ``None``.

    Args:
        **fields: Pasangan nama field dan nilai; ``None`` berarti tidak dikirim.

    Returns:
        Dict hanya berisi field yang nilainya bukan ``None``.
    """
    return {k: v for k, v in fields.items() if v is not None}


def register(mcp: FastMCP, client: AuthentikClient) -> None:
    """Daftarkan tool domain Source (baca dan tulis) ke server MCP.

    Args:
        mcp: Instance FastMCP.
        client: Klien Authentik bersama.
    """

    @mcp.tool(tags={"sources"})
    async def authentik_source_list(
        search: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Daftar seluruh source (semua tipe) dengan paginasi.

        Args:
            search: Kata kunci pencarian.
            page: Nomor halaman.
            page_size: Jumlah item per halaman.

        Returns:
            Objek paginasi berisi ``results`` dan ``pagination``.

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        params = {"search": search, "page": page, "page_size": page_size}
        return _strip_secrets(await client.get("/sources/all/", params=params))

    @mcp.tool(tags={"sources"})
    async def authentik_source_oauth_list(
        search: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Daftar source OAuth (mis. login Google) dengan paginasi.

        Args:
            search: Kata kunci pencarian.
            page: Nomor halaman.
            page_size: Jumlah item per halaman.

        Returns:
            Objek paginasi berisi ``results`` dan ``pagination``; ``consumer_secret``
            dibuang bila ada.

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        params = {"search": search, "page": page, "page_size": page_size}
        return _strip_secrets(await client.get("/sources/oauth/", params=params))

    @mcp.tool(tags={"sources"})
    async def authentik_source_oauth_get(slug: str) -> dict[str, Any]:
        """Ambil detail satu source OAuth berdasarkan slug.

        Args:
            slug: Slug unik source OAuth.

        Returns:
            Objek source OAuth tanpa ``consumer_secret``.

        Raises:
            AuthentikAPIError: 404 bila source tidak ditemukan.
        """
        return _strip_secrets(await client.get(f"/sources/oauth/{slug}/"))

    @mcp.tool(tags={"sources"})
    async def authentik_source_connection_list(
        source_slug: str | None = None,
        user: int | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Daftar koneksi user ke source OAuth.

        Args:
            source_slug: Filter berdasarkan slug source (query ``source__slug``).
            user: Filter berdasarkan pk user.
            page: Nomor halaman.
            page_size: Jumlah item per halaman.

        Returns:
            Objek paginasi berisi ``results`` dan ``pagination``.

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        params = {
            "source__slug": source_slug,
            "user": user,
            "page": page,
            "page_size": page_size,
        }
        return _strip_secrets(await client.get("/sources/user_connections/oauth/", params=params))

    @mcp.tool(tags={"sources"})
    async def authentik_source_oauth_create(
        name: str,
        slug: str,
        provider_type: str,
        consumer_key: str,
        consumer_secret: str,
        enabled: bool | None = None,
        promoted: bool | None = None,
        user_matching_mode: str = "identifier",
        authentication_flow: str | None = None,
        enrollment_flow: str | None = None,
        additional_scopes: str | None = None,
    ) -> dict[str, Any]:
        """Buat source OAuth baru (mis. login Google).

        PERINGATAN RAHASIA: ``consumer_secret`` adalah argumen tool sehingga bisa
        terekam di transkrip client MCP. Bila perekaman itu tidak dikehendaki,
        isi rahasia lewat Admin UI Authentik. Tool ini tidak pernah mengembalikan
        ``consumer_secret`` di keluaran maupun pesan error.

        Bawaan aman: ``user_matching_mode="identifier"`` dan tanpa
        ``enrollment_flow``, sehingga source tidak membuat akun baru dan tidak
        mencocokkan akun lewat email. Ubah hanya dengan argumen eksplisit.

        Args:
            name: Nama tampilan source.
            slug: Slug unik source.
            provider_type: Tipe provider OAuth (mis. ``google``, ``github``).
            consumer_key: Client ID dari penyedia OAuth.
            consumer_secret: Client secret dari penyedia OAuth (lihat peringatan).
            enabled: Aktif atau tidak; ``None`` memakai bawaan Authentik.
            promoted: Tampilkan sebagai tombol utama; ``None`` memakai bawaan.
            user_matching_mode: Cara mencocokkan user (``identifier``,
                ``email_link``, ``email_deny``, ``username_link``, ``username_deny``).
                Bawaan ``identifier``.
            authentication_flow: Slug flow autentikasi; ``None`` tidak dikirim.
            enrollment_flow: Slug flow pendaftaran; ``None`` tidak dikirim (tanpa
                pembuatan akun otomatis).
            additional_scopes: Scope tambahan dipisah spasi; ``None`` tidak dikirim.

        Returns:
            Objek source OAuth yang dibuat, tanpa ``consumer_secret``.

        Raises:
            AuthentikAPIError: 422 bila validasi gagal; nilai rahasia disamarkan.
        """
        payload = _source_payload(
            name=name,
            slug=slug,
            provider_type=provider_type,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            enabled=enabled,
            promoted=promoted,
            user_matching_mode=user_matching_mode,
            authentication_flow=authentication_flow,
            enrollment_flow=enrollment_flow,
            additional_scopes=additional_scopes,
        )
        try:
            result = await client.post("/sources/oauth/", json=payload)
        except AuthentikAPIError as exc:
            raise _redact_error(exc, consumer_secret) from None
        return _strip_secrets(result)

    @mcp.tool(tags={"sources"})
    async def authentik_source_oauth_update(
        slug: str,
        name: str | None = None,
        provider_type: str | None = None,
        consumer_key: str | None = None,
        consumer_secret: str | None = None,
        enabled: bool | None = None,
        promoted: bool | None = None,
        user_matching_mode: str | None = None,
        authentication_flow: str | None = None,
        enrollment_flow: str | None = None,
        additional_scopes: str | None = None,
    ) -> dict[str, Any]:
        """Perbarui sebagian field source OAuth (PATCH). Hanya argumen non-None dikirim.

        Nilai ``None`` berarti "tidak diubah", bukan "kosongkan".

        PERINGATAN RAHASIA: ``consumer_secret`` adalah argumen tool sehingga bisa
        terekam di transkrip client MCP. Bila tidak dikehendaki, ubah rahasia lewat
        Admin UI. Rahasia tidak pernah muncul di keluaran maupun pesan error.

        Args:
            slug: Slug source yang diperbarui.
            name: Nama tampilan baru.
            provider_type: Tipe provider baru.
            consumer_key: Client ID baru.
            consumer_secret: Client secret baru (lihat peringatan).
            enabled: Status aktif baru.
            promoted: Status promoted baru.
            user_matching_mode: Mode pencocokan user baru.
            authentication_flow: Slug flow autentikasi baru.
            enrollment_flow: Slug flow pendaftaran baru.
            additional_scopes: Scope tambahan baru.

        Returns:
            Objek source setelah diperbarui, tanpa ``consumer_secret``.

        Raises:
            ValueError: Bila tidak ada argumen perubahan; API tidak dipanggil.
            AuthentikAPIError: 404 bila source tidak ada, 422 bila validasi gagal.
        """
        payload = _source_payload(
            name=name,
            provider_type=provider_type,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            enabled=enabled,
            promoted=promoted,
            user_matching_mode=user_matching_mode,
            authentication_flow=authentication_flow,
            enrollment_flow=enrollment_flow,
            additional_scopes=additional_scopes,
        )
        if not payload:
            raise ValueError("Tidak ada field yang diberikan untuk diperbarui.")
        try:
            result = await client.patch(f"/sources/oauth/{slug}/", json=payload)
        except AuthentikAPIError as exc:
            raise _redact_error(exc, consumer_secret) from None
        return _strip_secrets(result)

    @mcp.tool(tags={"sources"})
    async def authentik_source_oauth_delete(slug: str) -> dict[str, str]:
        """Hapus source OAuth secara permanen.

        Args:
            slug: Slug source yang dihapus.

        Returns:
            Konfirmasi berisi ``status`` dan ``slug``.

        Raises:
            AuthentikAPIError: 404 bila source tidak ditemukan.
        """
        await client.delete(f"/sources/oauth/{slug}/")
        return {"status": "deleted", "slug": slug}
