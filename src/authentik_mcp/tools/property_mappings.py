"""Tool MCP untuk mengelola Property Mapping Authentik (CRUD per tipe).

Mendaftarkan tool:
- list & get & test via endpoint generik ``/propertymappings/all/`` (lintas tipe).
- create / update / delete per tipe property mapping (provider scope/saml/scim/
  rac/radius/google_workspace/microsoft_entra, source ldap/oauth/plex/saml/scim/
  kerberos/telegram, dan notification).
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import AuthentikClient

# Pemetaan tipe property mapping -> path endpoint Authentik (relatif /api/v3).
_PM_PATHS: dict[str, str] = {
    # Provider mappings
    "provider_scope": "/propertymappings/provider/scope/",
    "provider_saml": "/propertymappings/provider/saml/",
    "provider_scim": "/propertymappings/provider/scim/",
    "provider_rac": "/propertymappings/provider/rac/",
    "provider_radius": "/propertymappings/provider/radius/",
    "provider_google_workspace": "/propertymappings/provider/google_workspace/",
    "provider_microsoft_entra": "/propertymappings/provider/microsoft_entra/",
    # Source mappings
    "source_ldap": "/propertymappings/source/ldap/",
    "source_oauth": "/propertymappings/source/oauth/",
    "source_plex": "/propertymappings/source/plex/",
    "source_saml": "/propertymappings/source/saml/",
    "source_scim": "/propertymappings/source/scim/",
    "source_kerberos": "/propertymappings/source/kerberos/",
    "source_telegram": "/propertymappings/source/telegram/",
    # Notification mapping
    "notification": "/propertymappings/notification/",
}

# Field wajib di payload create per tipe (selain ``name`` & ``expression`` yang
# divalidasi terpisah). Kunci yang tidak ada di sini hanya butuh name+expression.
_PM_REQUIRED: dict[str, list[str]] = {
    "provider_scope": ["scope_name"],
    "provider_saml": ["saml_name"],
    "provider_rac": ["static_settings"],
}


def _validate_pm_type(mapping_type: str) -> str:
    """Validasi dan normalisasi mapping_type; raise ValueError bila tidak dikenal."""
    key = mapping_type.strip().lower()
    if key not in _PM_PATHS:
        valid = ", ".join(sorted(_PM_PATHS))
        raise ValueError(f"mapping_type tidak valid: {mapping_type!r}. Pilih salah satu: {valid}.")
    return key


def register(mcp: FastMCP, client: AuthentikClient) -> None:
    """Daftarkan seluruh tool domain Property Mapping ke server MCP.

    Args:
        mcp: Instance FastMCP.
        client: Klien Authentik bersama.
    """

    @mcp.tool(tags={"property_mappings"})
    async def authentik_property_mapping_list(
        search: str | None = None,
        managed_isnull: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Daftar SEMUA property mapping (lintas tipe) via ``/propertymappings/all/``.

        Args:
            search: Kata kunci pencarian nama property mapping.
            managed_isnull: Bila True, hanya tampilkan mapping kustom (bukan bawaan
                yang dikelola sistem); bila False, hanya yang dikelola sistem.
            page: Nomor halaman.
            page_size: Jumlah item per halaman.

        Returns:
            Objek paginasi berisi ``results`` (daftar property mapping).

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        params = {
            "search": search,
            "managed__isnull": managed_isnull,
            "page": page,
            "page_size": page_size,
        }
        return await client.get("/propertymappings/all/", params=params)

    @mcp.tool(tags={"property_mappings"})
    async def authentik_property_mapping_get(pm_uuid: str) -> dict[str, Any]:
        """Ambil detail satu property mapping berdasarkan UUID.

        Args:
            pm_uuid: UUID (pk) property mapping.

        Returns:
            Objek property mapping lengkap (termasuk ekspresi).

        Raises:
            AuthentikAPIError: 404 bila property mapping tidak ditemukan.
        """
        return await client.get(f"/propertymappings/all/{pm_uuid}/")

    @mcp.tool(tags={"property_mappings"})
    async def authentik_property_mapping_create(
        mapping_type: str,
        name: str,
        expression: str,
        scope_name: str | None = None,
        saml_name: str | None = None,
        extra_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Buat property mapping baru sesuai tipenya.

        Semua tipe membutuhkan ``name`` dan ``expression``. Field tambahan wajib:

        - **provider_scope**: ``scope_name`` wajib — nama scope OAuth2/OIDC.
        - **provider_saml**: ``saml_name`` wajib — nama atribut SAML.
        - Tipe lain hanya butuh ``name`` + ``expression``; gunakan ``extra_config``
          untuk field spesifik (mis. ``friendly_name`` pada SAML).

        Args:
            mapping_type: Kunci tipe mapping, mis. ``provider_scope``,
                ``provider_saml``, ``provider_scim``, ``provider_rac``,
                ``provider_radius``, ``provider_google_workspace``,
                ``provider_microsoft_entra``, ``source_ldap``, ``source_oauth``,
                ``source_plex``, ``source_saml``, ``source_scim``,
                ``source_kerberos``, ``source_telegram``, atau ``notification``.
            name: Nama unik property mapping.
            expression: Ekspresi Python yang dievaluasi mapping.
            scope_name: *(provider_scope)* Nama scope OAuth2/OIDC.
            saml_name: *(provider_saml)* Nama atribut SAML (URN/URI).
            extra_config: Field tambahan opsional sesuai tipe.

        Returns:
            Objek property mapping yang baru dibuat (termasuk ``pk``).

        Raises:
            ValueError: Bila ``mapping_type`` tidak dikenal atau field wajib
                per tipe tidak lengkap.
            AuthentikAPIError: 422 bila validasi Authentik gagal.
        """
        key = _validate_pm_type(mapping_type)

        payload: dict[str, Any] = {"name": name, "expression": expression}
        for field, value in {"scope_name": scope_name, "saml_name": saml_name}.items():
            if value is not None:
                payload[field] = value
        if extra_config:
            payload.update(extra_config)

        missing = [f for f in _PM_REQUIRED.get(key, []) if f not in payload]
        if missing:
            raise ValueError(
                f"Property mapping tipe {key!r} membutuhkan field: {', '.join(missing)}."
            )

        return await client.post(_PM_PATHS[key], json=payload)

    @mcp.tool(tags={"property_mappings"})
    async def authentik_property_mapping_update(
        mapping_type: str,
        pm_uuid: str,
        name: str | None = None,
        expression: str | None = None,
        scope_name: str | None = None,
        saml_name: str | None = None,
        extra_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Perbarui sebagian field property mapping (PATCH). Hanya field non-None dikirim.

        Args:
            mapping_type: Kunci tipe mapping (lihat ``authentik_property_mapping_create``).
            pm_uuid: UUID property mapping.
            name: Nama baru.
            expression: Ekspresi Python baru.
            scope_name: *(provider_scope)* Nama scope baru.
            saml_name: *(provider_saml)* Nama atribut SAML baru.
            extra_config: Field tambahan opsional yang ingin diubah.

        Returns:
            Objek property mapping setelah diperbarui.

        Raises:
            ValueError: Bila ``mapping_type`` tidak dikenal atau tidak ada field
                yang diberikan.
            AuthentikAPIError: 404 bila property mapping tidak ditemukan.
        """
        key = _validate_pm_type(mapping_type)

        payload: dict[str, Any] = {}
        for field, value in {
            "name": name,
            "expression": expression,
            "scope_name": scope_name,
            "saml_name": saml_name,
        }.items():
            if value is not None:
                payload[field] = value
        if extra_config:
            payload.update(extra_config)

        if not payload:
            raise ValueError("Tidak ada field yang diberikan untuk diperbarui.")

        return await client.patch(f"{_PM_PATHS[key]}{pm_uuid}/", json=payload)

    @mcp.tool(tags={"property_mappings"})
    async def authentik_property_mapping_delete(pm_uuid: str) -> dict[str, str]:
        """Hapus property mapping secara permanen via endpoint generik ``/propertymappings/all/``.

        Args:
            pm_uuid: UUID property mapping (berlaku untuk semua tipe).

        Returns:
            Konfirmasi penghapusan.

        Raises:
            AuthentikAPIError: 404 bila property mapping tidak ditemukan.
        """
        await client.delete(f"/propertymappings/all/{pm_uuid}/")
        return {"status": "deleted", "pm_uuid": pm_uuid}

    @mcp.tool(tags={"property_mappings"})
    async def authentik_property_mapping_test(
        pm_uuid: str,
        user_id: int | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Uji evaluasi property mapping (jalankan ekspresinya).

        Args:
            pm_uuid: UUID property mapping yang diuji.
            user_id: pk numerik user sebagai konteks evaluasi (opsional).
            context: Konteks tambahan yang diteruskan ke mapping (opsional).

        Returns:
            Hasil evaluasi berisi ``result`` dan/atau ``successful``.

        Raises:
            AuthentikAPIError: 404 bila property mapping tidak ditemukan.
        """
        payload: dict[str, Any] = {}
        if user_id is not None:
            payload["user"] = user_id
        if context is not None:
            payload["context"] = context
        return await client.post(f"/propertymappings/all/{pm_uuid}/test/", json=payload)
