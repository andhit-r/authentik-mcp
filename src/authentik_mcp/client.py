"""Klien HTTP async untuk Authentik REST API (v3).

Modul ini membungkus ``httpx.AsyncClient`` dan menyediakan:

* Penambahan otomatis header ``Authorization: Bearer <AUTHENTIK_API_TOKEN>``.
* Penanganan eksplisit untuk HTTP error umum dari Authentik (401, 403, 404,
  422, 500) dengan pesan yang informatif melalui :class:`AuthentikAPIError`.
* Helper ``get/post/patch/put/delete`` serta ``paginate`` untuk endpoint
  list Authentik yang menggunakan paginasi.

Klien ini dipakai bersama (shared) oleh seluruh tool MCP agar koneksi HTTP
dapat di-pool dan dikelola siklus hidupnya secara terpusat.
"""

from __future__ import annotations

from typing import Any

import httpx

from .config import Settings


class AuthentikAPIError(Exception):
    """Error yang dilempar ketika request ke Authentik API gagal.

    Pesan dibuat informatif sesuai status code agar pemanggil (dan AI) dapat
    memahami penyebab kegagalan.

    Attributes:
        status_code: HTTP status code dari respons Authentik (``None`` bila
            kegagalan terjadi sebelum respons diterima, mis. error jaringan).
        detail: Detail tambahan dari body respons Authentik (bila ada).
        method: Metode HTTP yang digunakan.
        path: Path API yang dipanggil.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        detail: Any = None,
        method: str | None = None,
        path: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.detail = detail
        self.method = method
        self.path = path
        super().__init__(message)


# Pesan ramah per status code yang sering muncul dari Authentik API.
_STATUS_HINTS: dict[int, str] = {
    400: "Permintaan tidak valid (400). Periksa parameter yang dikirim.",
    401: (
        "Tidak terautentikasi (401). AUTHENTIK_API_TOKEN salah, kedaluwarsa, atau tidak dikirim."
    ),
    403: ("Akses ditolak (403). Token tidak memiliki izin yang cukup untuk resource ini."),
    404: "Resource tidak ditemukan (404). Periksa ID/slug/identifier yang dipakai.",
    409: "Konflik (409). Resource mungkin sudah ada atau melanggar batasan unik.",
    422: ("Validasi gagal (422). Data yang dikirim tidak memenuhi skema Authentik."),
    500: "Kesalahan internal server Authentik (500). Coba lagi atau cek log Authentik.",
}


class AuthentikClient:
    """Klien async untuk berinteraksi dengan Authentik REST API.

    Gunakan sebagai async context manager atau panggil :meth:`aclose` saat
    selesai untuk menutup koneksi.

    Example:
        >>> settings = get_settings()
        >>> async with AuthentikClient(settings) as client:
        ...     users = await client.get("/core/users/")
    """

    def __init__(
        self,
        settings: Settings,
        *,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Inisialisasi klien.

        Args:
            settings: Konfigurasi aplikasi (URL & token Authentik).
            http_client: ``httpx.AsyncClient`` opsional untuk injeksi (berguna
                pada unit test). Bila ``None``, klien internal dibuat otomatis.
        """
        self._settings = settings
        self._owns_client = http_client is None
        token = settings.authentik_api_token.get_secret_value()
        self._client = http_client or httpx.AsyncClient(
            base_url=settings.api_base_url,
            timeout=settings.authentik_timeout,
            verify=settings.authentik_verify_ssl,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )

    async def __aenter__(self) -> AuthentikClient:
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Tutup koneksi HTTP bila klien ini yang membuatnya."""
        if self._owns_client:
            await self._client.aclose()

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
    ) -> Any:
        """Kirim satu request ke Authentik API dan kembalikan body terurai.

        Args:
            method: Metode HTTP (``GET``, ``POST``, ``PATCH``, ``PUT``, ``DELETE``).
            path: Path relatif terhadap ``/api/v3`` (mis. ``/core/users/``).
            params: Query parameter opsional. Nilai ``None`` akan dibuang.
            json: Body JSON opsional untuk request yang mengubah data.

        Returns:
            Body respons yang sudah di-decode JSON. Untuk respons ``204 No
            Content`` (mis. DELETE), mengembalikan ``None``.

        Raises:
            AuthentikAPIError: Bila respons memiliki status error (>= 400) atau
                terjadi error jaringan/timeout.
        """
        clean_params = {k: v for k, v in params.items() if v is not None} if params else None
        try:
            response = await self._client.request(
                method.upper(), path, params=clean_params, json=json
            )
        except httpx.TimeoutException as exc:
            raise AuthentikAPIError(
                f"Timeout saat memanggil Authentik API ({method} {path}).",
                method=method,
                path=path,
            ) from exc
        except httpx.RequestError as exc:
            raise AuthentikAPIError(
                f"Gagal terhubung ke Authentik API ({method} {path}): {exc}",
                method=method,
                path=path,
            ) from exc

        if response.is_error:
            self._raise_for_status(response, method, path)

        if response.status_code == 204 or not response.content:
            return None
        try:
            return response.json()
        except ValueError:
            # Respons bukan JSON (jarang terjadi); kembalikan teks mentah.
            return response.text

    @staticmethod
    def _raise_for_status(response: httpx.Response, method: str, path: str) -> None:
        """Terjemahkan respons error HTTP menjadi :class:`AuthentikAPIError`.

        Args:
            response: Respons httpx dengan status >= 400.
            method: Metode HTTP yang dipakai.
            path: Path API yang dipanggil.

        Raises:
            AuthentikAPIError: Selalu dilempar dengan pesan sesuai status code.
        """
        status = response.status_code
        detail: Any = None
        try:
            detail = response.json()
        except ValueError:
            detail = response.text or None

        hint = _STATUS_HINTS.get(status, f"Authentik API mengembalikan status {status}.")
        message = f"{hint} ({method} {path})"
        if detail:
            message = f"{message} Detail: {detail}"
        raise AuthentikAPIError(
            message, status_code=status, detail=detail, method=method, path=path
        )

    # --- Helper metode HTTP ---

    async def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        """Lakukan GET request. Lihat :meth:`request`."""
        return await self.request("GET", path, params=params)

    async def post(self, path: str, *, json: Any = None) -> Any:
        """Lakukan POST request. Lihat :meth:`request`."""
        return await self.request("POST", path, json=json)

    async def patch(self, path: str, *, json: Any = None) -> Any:
        """Lakukan PATCH request. Lihat :meth:`request`."""
        return await self.request("PATCH", path, json=json)

    async def put(self, path: str, *, json: Any = None) -> Any:
        """Lakukan PUT request. Lihat :meth:`request`."""
        return await self.request("PUT", path, json=json)

    async def delete(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        """Lakukan DELETE request. Lihat :meth:`request`."""
        return await self.request("DELETE", path, params=params)
