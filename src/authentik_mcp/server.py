"""Perakitan server FastMCP authentik-mcp.

Modul ini menyatukan seluruh komponen:

* memuat konfigurasi (:mod:`authentik_mcp.config`),
* membangun klien Authentik (:mod:`authentik_mcp.client`),
* menyiapkan proteksi OAuth (:mod:`authentik_mcp.auth`),
* mendaftarkan seluruh tool domain (:mod:`authentik_mcp.tools`),
* menambahkan rute dokumentasi Swagger (:mod:`authentik_mcp.docs`).

Fungsi utama: :func:`create_server` (membangun instance) dan :func:`run`
(menjalankan server sesuai transport yang dikonfigurasi).
"""

from __future__ import annotations

from fastmcp import FastMCP

from . import __version__
from .auth import build_token_verifier
from .client import AuthentikClient
from .config import Settings, get_settings
from .docs import register_docs_routes
from .logging import configure_logging, get_logger
from .tools import register_all

logger = get_logger(__name__)

_INSTRUCTIONS = (
    "Server MCP untuk mengelola Authentik melalui REST API. Tool tersedia untuk "
    "mengelola users, groups, applications, providers, tokens, events, flows, "
    "property mappings, dan outposts. Semua tool diawali prefix `authentik_`."
)


def create_server(settings: Settings | None = None) -> FastMCP:
    """Bangun dan kembalikan instance FastMCP yang sudah terkonfigurasi penuh.

    Args:
        settings: Konfigurasi opsional. Bila ``None``, dimuat dari environment.

    Returns:
        Instance ``FastMCP`` siap dijalankan, dengan seluruh tool, proteksi
        OAuth (bila dikonfigurasi), dan rute dokumentasi telah terpasang.

    Raises:
        ValueError: Bila konfigurasi wajib Authentik API belum lengkap.
    """
    settings = settings or get_settings()
    settings.require_api_config()

    auth = build_token_verifier(settings)
    mcp = FastMCP(
        name="authentik-mcp",
        version=__version__,
        instructions=_INSTRUCTIONS,
        auth=auth,
    )

    client = AuthentikClient(settings)
    register_all(mcp, client)
    register_docs_routes(mcp, __version__)

    logger.info(
        "authentik-mcp v%s siap. Target Authentik: %s",
        __version__,
        settings.authentik_url,
    )
    return mcp


def run(settings: Settings | None = None) -> None:
    """Jalankan server MCP sesuai transport yang dikonfigurasi.

    Args:
        settings: Konfigurasi opsional. Bila ``None``, dimuat dari environment.

    Raises:
        ValueError: Bila konfigurasi wajib belum lengkap.
    """
    settings = settings or get_settings()
    configure_logging(settings.mcp_log_level)
    mcp = create_server(settings)

    if settings.mcp_transport == "stdio":
        logger.info("Menjalankan transport stdio.")
        mcp.run(transport="stdio")
    else:
        logger.info(
            "Menjalankan transport HTTP di %s:%s (docs: /docs).",
            settings.mcp_host,
            settings.mcp_port,
        )
        mcp.run(
            transport="http",
            host=settings.mcp_host,
            port=settings.mcp_port,
            log_level=settings.mcp_log_level,
        )
