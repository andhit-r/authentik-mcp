"""Konfigurasi aplikasi dari environment variable.

Seluruh konfigurasi authentik-mcp dibaca dari environment variable (atau file
``.env``) menggunakan ``pydantic-settings``. Tidak ada credential atau URL yang
di-hardcode di dalam kode.

Penggunaan::

    from authentik_mcp.config import get_settings

    settings = get_settings()
    print(settings.authentik_url)
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Kumpulan konfigurasi authentik-mcp.

    Atribut dipetakan dari environment variable dengan nama uppercase yang sama
    (case-insensitive). Nilai sensitif (token, secret) disimpan sebagai
    ``SecretStr`` agar tidak ikut tercetak saat objek di-repr/di-log.

    Attributes:
        authentik_url: URL dasar instance Authentik, mis. ``https://auth.example.com``.
            Trailing slash akan dihapus otomatis.
        authentik_api_token: API Token Authentik untuk header ``Authorization: Bearer``.
        authentik_timeout: Timeout (detik) tiap request ke Authentik API.
        authentik_verify_ssl: Apakah memverifikasi sertifikat TLS Authentik.
        oauth_introspection_url: Endpoint introspection OAuth Authentik
            (``/application/o/introspect/``). Kosong = autentikasi MCP dinonaktifkan.
        oauth_client_id: Client ID OAuth provider untuk introspeksi token.
        oauth_client_secret: Client Secret OAuth provider untuk introspeksi token.
        oauth_required_scopes: Daftar scope (dipisah spasi) yang wajib dimiliki token.
        oauth_cache_ttl: TTL (detik) cache hasil introspeksi (0 = nonaktif).
        mcp_transport: Transport FastMCP: ``http`` atau ``stdio``.
        mcp_host: Host bind saat transport http.
        mcp_port: Port bind saat transport http.
        mcp_log_level: Level logging.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Koneksi Authentik API ---
    authentik_url: str = Field(default="", description="URL dasar instance Authentik.")
    authentik_api_token: SecretStr = Field(
        default=SecretStr(""), description="API Token Authentik."
    )
    authentik_timeout: float = Field(default=30.0, ge=1.0)
    authentik_verify_ssl: bool = Field(default=True)

    # --- Proteksi OAuth untuk MCP server ---
    oauth_introspection_url: str = Field(default="")
    oauth_client_id: str = Field(default="")
    oauth_client_secret: SecretStr = Field(default=SecretStr(""))
    oauth_required_scopes: str = Field(default="")
    oauth_cache_ttl: int = Field(default=0, ge=0)

    # --- Runtime MCP ---
    mcp_transport: str = Field(default="http")
    mcp_host: str = Field(default="0.0.0.0")
    mcp_port: int = Field(default=8000, ge=1, le=65535)
    mcp_log_level: str = Field(default="INFO")

    @field_validator("authentik_url", "oauth_introspection_url")
    @classmethod
    def _strip_trailing_slash(cls, value: str) -> str:
        """Hapus trailing slash agar penggabungan path konsisten."""
        return value.rstrip("/") if value else value

    @field_validator("mcp_transport")
    @classmethod
    def _validate_transport(cls, value: str) -> str:
        """Pastikan transport yang dipilih didukung."""
        allowed = {"http", "stdio"}
        normalized = value.strip().lower()
        if normalized not in allowed:
            raise ValueError(
                f"MCP_TRANSPORT tidak valid: {value!r}. Pilih salah satu dari {allowed}."
            )
        return normalized

    @property
    def api_base_url(self) -> str:
        """URL dasar REST API Authentik (v3), mis. ``https://auth.example.com/api/v3``."""
        return f"{self.authentik_url}/api/v3"

    @property
    def oauth_enabled(self) -> bool:
        """True bila konfigurasi OAuth introspection lengkap.

        MCP server hanya mengaktifkan proteksi autentikasi bila ketiga nilai
        (introspection URL, client id, client secret) tersedia.
        """
        return bool(
            self.oauth_introspection_url
            and self.oauth_client_id
            and self.oauth_client_secret.get_secret_value()
        )

    @property
    def required_scopes_list(self) -> list[str]:
        """Daftar scope wajib hasil parsing string ``oauth_required_scopes``."""
        return [s for s in self.oauth_required_scopes.split() if s]

    def require_api_config(self) -> None:
        """Validasi bahwa konfigurasi minimum Authentik API tersedia.

        Raises:
            ValueError: Bila ``AUTHENTIK_URL`` atau ``AUTHENTIK_API_TOKEN`` kosong.
        """
        missing = []
        if not self.authentik_url:
            missing.append("AUTHENTIK_URL")
        if not self.authentik_api_token.get_secret_value():
            missing.append("AUTHENTIK_API_TOKEN")
        if missing:
            raise ValueError(
                "Konfigurasi wajib belum diisi: " + ", ".join(missing) + ". "
                "Set environment variable tersebut atau isi file .env."
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Kembalikan instance ``Settings`` singleton (di-cache).

    Returns:
        Objek ``Settings`` yang dibaca dari environment/``.env``.
    """
    return Settings()
