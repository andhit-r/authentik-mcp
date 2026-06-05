"""Tool MCP untuk mengelola Certificate-Key Pair Authentik (kriptografi).

Mendaftarkan tool untuk endpoint ``/crypto/certificatekeypairs/``: list, get,
create (impor PEM), generate (terbitkan sertifikat self-signed), update, delete,
serta melihat isi sertifikat dan private key.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import AuthentikClient

_BASE = "/crypto/certificatekeypairs/"


def register(mcp: FastMCP, client: AuthentikClient) -> None:
    """Daftarkan seluruh tool domain Crypto (certificate-key pair) ke server MCP.

    Args:
        mcp: Instance FastMCP.
        client: Klien Authentik bersama.
    """

    @mcp.tool(tags={"crypto"})
    async def authentik_certificate_list(
        search: str | None = None,
        name: str | None = None,
        has_key: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Daftar certificate-key pair dengan filter dan paginasi.

        Args:
            search: Kata kunci pencarian nama.
            name: Filter persis berdasarkan nama.
            has_key: Bila True, hanya pasangan yang memiliki private key.
            page: Nomor halaman.
            page_size: Jumlah item per halaman.

        Returns:
            Objek paginasi berisi ``results`` (daftar certificate-key pair).

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        params = {
            "search": search,
            "name": name,
            "has_key": has_key,
            "page": page,
            "page_size": page_size,
        }
        return await client.get(_BASE, params=params)

    @mcp.tool(tags={"crypto"})
    async def authentik_certificate_get(kp_uuid: str) -> dict[str, Any]:
        """Ambil detail satu certificate-key pair berdasarkan UUID.

        Args:
            kp_uuid: UUID (pk) certificate-key pair.

        Returns:
            Objek certificate-key pair (metadata sertifikat, masa berlaku, dll).

        Raises:
            AuthentikAPIError: 404 bila tidak ditemukan.
        """
        return await client.get(f"{_BASE}{kp_uuid}/")

    @mcp.tool(tags={"crypto"})
    async def authentik_certificate_create(
        name: str,
        certificate_data: str,
        key_data: str | None = None,
    ) -> dict[str, Any]:
        """Impor certificate-key pair dari data PEM.

        Args:
            name: Nama unik certificate-key pair.
            certificate_data: Isi sertifikat dalam format PEM.
            key_data: Isi private key dalam format PEM (opsional; boleh kosong
                untuk sertifikat verifikasi tanpa private key).

        Returns:
            Objek certificate-key pair yang baru dibuat (termasuk ``pk``).

        Raises:
            AuthentikAPIError: 422 bila PEM tidak valid.
        """
        payload: dict[str, Any] = {"name": name, "certificate_data": certificate_data}
        if key_data is not None:
            payload["key_data"] = key_data
        return await client.post(_BASE, json=payload)

    @mcp.tool(tags={"crypto"})
    async def authentik_certificate_generate(
        common_name: str,
        validity_days: int,
        subject_alt_name: str | None = None,
        alg: str | None = None,
    ) -> dict[str, Any]:
        """Terbitkan certificate-key pair self-signed baru.

        Args:
            common_name: Common Name (CN) sertifikat.
            validity_days: Masa berlaku sertifikat dalam hari.
            subject_alt_name: Subject Alternative Name, dipisah koma (opsional).
            alg: Algoritma kunci, mis. ``rsa`` atau ``ecdsa`` (opsional; default
                Authentik bila tidak diisi).

        Returns:
            Hasil pembuatan sertifikat (umumnya berisi ``certificate_key_pair``).

        Raises:
            AuthentikAPIError: 422 bila parameter tidak valid.
        """
        payload: dict[str, Any] = {
            "common_name": common_name,
            "validity_days": validity_days,
        }
        if subject_alt_name is not None:
            payload["subject_alt_name"] = subject_alt_name
        if alg is not None:
            payload["alg"] = alg
        return await client.post(f"{_BASE}generate/", json=payload)

    @mcp.tool(tags={"crypto"})
    async def authentik_certificate_update(
        kp_uuid: str,
        name: str | None = None,
        certificate_data: str | None = None,
        key_data: str | None = None,
    ) -> dict[str, Any]:
        """Perbarui sebagian field certificate-key pair (PATCH).

        Args:
            kp_uuid: UUID certificate-key pair.
            name: Nama baru.
            certificate_data: Data sertifikat PEM baru.
            key_data: Data private key PEM baru.

        Returns:
            Objek certificate-key pair setelah diperbarui.

        Raises:
            ValueError: Bila tidak ada field yang diberikan.
            AuthentikAPIError: 404 bila tidak ditemukan.
        """
        payload: dict[str, Any] = {}
        for field, value in {
            "name": name,
            "certificate_data": certificate_data,
            "key_data": key_data,
        }.items():
            if value is not None:
                payload[field] = value
        if not payload:
            raise ValueError("Tidak ada field yang diberikan untuk diperbarui.")
        return await client.patch(f"{_BASE}{kp_uuid}/", json=payload)

    @mcp.tool(tags={"crypto"})
    async def authentik_certificate_delete(kp_uuid: str) -> dict[str, str]:
        """Hapus certificate-key pair secara permanen.

        Args:
            kp_uuid: UUID certificate-key pair.

        Returns:
            Konfirmasi penghapusan.

        Raises:
            AuthentikAPIError: 404 bila tidak ditemukan.
        """
        await client.delete(f"{_BASE}{kp_uuid}/")
        return {"status": "deleted", "kp_uuid": kp_uuid}

    @mcp.tool(tags={"crypto"})
    async def authentik_certificate_view(kp_uuid: str) -> dict[str, Any]:
        """Lihat isi sertifikat (PEM) dari certificate-key pair.

        Args:
            kp_uuid: UUID certificate-key pair.

        Returns:
            Objek berisi ``data`` (sertifikat dalam format PEM).

        Raises:
            AuthentikAPIError: 404 bila tidak ditemukan.
        """
        return await client.get(f"{_BASE}{kp_uuid}/view_certificate/")

    @mcp.tool(tags={"crypto"})
    async def authentik_certificate_view_private_key(kp_uuid: str) -> dict[str, Any]:
        """Lihat isi private key (PEM) dari certificate-key pair.

        Args:
            kp_uuid: UUID certificate-key pair.

        Returns:
            Objek berisi ``data`` (private key dalam format PEM).

        Raises:
            AuthentikAPIError: 404 bila tidak ditemukan atau tidak memiliki key.
        """
        return await client.get(f"{_BASE}{kp_uuid}/view_private_key/")
