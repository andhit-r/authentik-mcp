"""Tool MCP untuk mengelola Brand Authentik (endpoint ``/core/brands/``).

Brand adalah pengaturan tampilan dan identitas per domain (judul, logo, favicon,
flow bawaan, sertifikat web). Mendaftarkan tool: list, get, create, update, delete.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import AuthentikClient

# Field ``BrandRequest`` (Authentik 2026.8.5) yang bernilai ``null`` valid, sehingga
# boleh dikosongkan lewat ``clear_fields`` pada update.
_NULLABLE_FIELDS = frozenset(
    {
        "flow_authentication",
        "flow_invalidation",
        "flow_recovery",
        "flow_user_settings",
        "flow_unenrollment",
        "flow_device_code",
        "flow_user_switch",
        "flow_lockdown",
        "flow_request",
        "default_application",
        "web_certificate",
    }
)


def _brand_payload(**fields: Any) -> dict[str, Any]:
    """Susun body request brand dari field yang diberikan.

    Args:
        **fields: Pasangan nama field dan nilainya.

    Returns:
        Dict berisi hanya field yang nilainya bukan ``None``.
    """
    return {key: value for key, value in fields.items() if value is not None}


def register(mcp: FastMCP, client: AuthentikClient) -> None:
    """Daftarkan seluruh tool domain Brand ke server MCP.

    Args:
        mcp: Instance FastMCP.
        client: Klien Authentik bersama.
    """

    @mcp.tool(tags={"brands"})
    async def authentik_brand_list(
        search: str | None = None,
        domain: str | None = None,
        default: bool | None = None,
        ordering: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Daftar brand dengan filter dan paginasi.

        Args:
            search: Kata kunci pencarian.
            domain: Filter berdasarkan domain.
            default: Filter brand bawaan (``True``/``False``); None = tidak difilter.
            ordering: Nama field pengurutan (awali ``-`` untuk menurun).
            page: Nomor halaman.
            page_size: Jumlah item per halaman.

        Returns:
            Objek paginasi berisi ``results`` (daftar brand) dan ``pagination``.

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        params: dict[str, Any] = {
            "search": search,
            "domain": domain,
            "ordering": ordering,
            "page": page,
            "page_size": page_size,
        }
        if default is not None:
            params["default"] = "true" if default else "false"
        return await client.get("/core/brands/", params=params)

    @mcp.tool(tags={"brands"})
    async def authentik_brand_get(brand_uuid: str) -> dict[str, Any]:
        """Ambil detail satu brand berdasarkan UUID.

        Args:
            brand_uuid: UUID brand.

        Returns:
            Objek brand lengkap.

        Raises:
            AuthentikAPIError: 404 bila brand tidak ditemukan.
        """
        return await client.get(f"/core/brands/{brand_uuid}/")

    @mcp.tool(tags={"brands"})
    async def authentik_brand_create(
        domain: str,
        default: bool | None = None,
        branding_title: str | None = None,
        branding_logo: str | None = None,
        branding_favicon: str | None = None,
        branding_custom_css: str | None = None,
        branding_default_flow_background: str | None = None,
        branding_map_tiles: str | None = None,
        flow_authentication: str | None = None,
        flow_invalidation: str | None = None,
        flow_recovery: str | None = None,
        flow_user_settings: str | None = None,
        flow_unenrollment: str | None = None,
        flow_device_code: str | None = None,
        flow_user_switch: str | None = None,
        flow_lockdown: str | None = None,
        flow_request: str | None = None,
        default_application: str | None = None,
        web_certificate: str | None = None,
        client_certificates: list[str] | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Buat brand baru. Hanya ``domain`` yang wajib; field None tidak dikirim.

        Args:
            domain: Domain yang dilayani brand ini.
            default: Jadikan brand bawaan.
            branding_title: Judul tampilan.
            branding_logo: Path/URL logo.
            branding_favicon: Path/URL favicon.
            branding_custom_css: CSS kustom.
            branding_default_flow_background: Path/URL latar belakang flow.
            branding_map_tiles: URL tile peta.
            flow_authentication: UUID flow autentikasi.
            flow_invalidation: UUID flow invalidasi sesi (logout).
            flow_recovery: UUID flow pemulihan akun.
            flow_user_settings: UUID flow pengaturan pengguna.
            flow_unenrollment: UUID flow unenrollment.
            flow_device_code: UUID flow device code.
            flow_user_switch: UUID flow pergantian pengguna.
            flow_lockdown: UUID flow lockdown.
            flow_request: UUID flow permintaan.
            default_application: UUID aplikasi bawaan.
            web_certificate: UUID sertifikat web.
            client_certificates: Daftar UUID sertifikat klien.
            attributes: Atribut bebas (dict).

        Returns:
            Objek brand yang baru dibuat.

        Raises:
            AuthentikAPIError: 422 bila validasi gagal.
        """
        payload = _brand_payload(
            domain=domain,
            default=default,
            branding_title=branding_title,
            branding_logo=branding_logo,
            branding_favicon=branding_favicon,
            branding_custom_css=branding_custom_css,
            branding_default_flow_background=branding_default_flow_background,
            branding_map_tiles=branding_map_tiles,
            flow_authentication=flow_authentication,
            flow_invalidation=flow_invalidation,
            flow_recovery=flow_recovery,
            flow_user_settings=flow_user_settings,
            flow_unenrollment=flow_unenrollment,
            flow_device_code=flow_device_code,
            flow_user_switch=flow_user_switch,
            flow_lockdown=flow_lockdown,
            flow_request=flow_request,
            default_application=default_application,
            web_certificate=web_certificate,
            client_certificates=client_certificates,
            attributes=attributes,
        )
        return await client.post("/core/brands/", json=payload)

    @mcp.tool(tags={"brands"})
    async def authentik_brand_update(
        brand_uuid: str,
        domain: str | None = None,
        default: bool | None = None,
        branding_title: str | None = None,
        branding_logo: str | None = None,
        branding_favicon: str | None = None,
        branding_custom_css: str | None = None,
        branding_default_flow_background: str | None = None,
        branding_map_tiles: str | None = None,
        flow_authentication: str | None = None,
        flow_invalidation: str | None = None,
        flow_recovery: str | None = None,
        flow_user_settings: str | None = None,
        flow_unenrollment: str | None = None,
        flow_device_code: str | None = None,
        flow_user_switch: str | None = None,
        flow_lockdown: str | None = None,
        flow_request: str | None = None,
        default_application: str | None = None,
        web_certificate: str | None = None,
        client_certificates: list[str] | None = None,
        attributes: dict[str, Any] | None = None,
        clear_fields: list[str] | None = None,
    ) -> dict[str, Any]:
        """Perbarui sebagian field brand (PATCH). Hanya field non-None dikirim.

        Args:
            brand_uuid: UUID brand yang diperbarui.
            domain: Domain baru.
            default: Status brand bawaan.
            branding_title: Judul baru.
            branding_logo: Logo baru.
            branding_favicon: Favicon baru.
            branding_custom_css: CSS kustom baru.
            branding_default_flow_background: Latar belakang flow baru.
            branding_map_tiles: URL tile peta baru.
            flow_authentication: UUID flow autentikasi baru.
            flow_invalidation: UUID flow invalidasi baru.
            flow_recovery: UUID flow pemulihan baru.
            flow_user_settings: UUID flow pengaturan pengguna baru.
            flow_unenrollment: UUID flow unenrollment baru.
            flow_device_code: UUID flow device code baru.
            flow_user_switch: UUID flow pergantian pengguna baru.
            flow_lockdown: UUID flow lockdown baru.
            flow_request: UUID flow permintaan baru.
            default_application: UUID aplikasi bawaan baru.
            web_certificate: UUID sertifikat web baru.
            client_certificates: Daftar UUID sertifikat klien baru.
            attributes: Atribut baru (menggantikan nilai lama).
            clear_fields: Nama field nullable yang dikosongkan (dikirim ``null``);
                hanya field ``flow_*``, ``default_application``, ``web_certificate``.

        Returns:
            Objek brand setelah diperbarui.

        Raises:
            ValueError: Bila ``clear_fields`` memuat field non-nullable, atau tidak
                ada field sama sekali yang diberikan (tanpa request HTTP).
            AuthentikAPIError: 404 bila tidak ditemukan, 422 bila validasi gagal.
        """
        invalid = sorted(set(clear_fields or []) - _NULLABLE_FIELDS)
        if invalid:
            raise ValueError(
                f"Field tidak dapat dikosongkan: {', '.join(invalid)}. "
                f"Yang diizinkan: {', '.join(sorted(_NULLABLE_FIELDS))}."
            )
        payload = _brand_payload(
            domain=domain,
            default=default,
            branding_title=branding_title,
            branding_logo=branding_logo,
            branding_favicon=branding_favicon,
            branding_custom_css=branding_custom_css,
            branding_default_flow_background=branding_default_flow_background,
            branding_map_tiles=branding_map_tiles,
            flow_authentication=flow_authentication,
            flow_invalidation=flow_invalidation,
            flow_recovery=flow_recovery,
            flow_user_settings=flow_user_settings,
            flow_unenrollment=flow_unenrollment,
            flow_device_code=flow_device_code,
            flow_user_switch=flow_user_switch,
            flow_lockdown=flow_lockdown,
            flow_request=flow_request,
            default_application=default_application,
            web_certificate=web_certificate,
            client_certificates=client_certificates,
            attributes=attributes,
        )
        for name in clear_fields or []:
            payload[name] = None
        if not payload:
            raise ValueError("Tidak ada field yang diberikan untuk diperbarui.")
        return await client.patch(f"/core/brands/{brand_uuid}/", json=payload)

    @mcp.tool(tags={"brands"})
    async def authentik_brand_delete(brand_uuid: str) -> dict[str, str]:
        """Hapus brand secara permanen.

        Args:
            brand_uuid: UUID brand.

        Returns:
            Konfirmasi penghapusan.

        Raises:
            AuthentikAPIError: 404 bila brand tidak ditemukan.
        """
        await client.delete(f"/core/brands/{brand_uuid}/")
        return {"status": "deleted", "brand_uuid": brand_uuid}
