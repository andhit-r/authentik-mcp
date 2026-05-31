"""authentik-mcp.

MCP (Model Context Protocol) server untuk mengelola Authentik melalui REST API,
dibangun di atas FastMCP.

Modul-modul penting:
    - ``config``  : pemuatan konfigurasi dari environment variable.
    - ``client``  : klien HTTP async ke Authentik API beserta penanganan error.
    - ``auth``    : pembentukan verifier OAuth (RFC 7662 introspection).
    - ``server``  : perakitan instance FastMCP dan registrasi seluruh tool.
    - ``tools``   : implementasi tool per domain Authentik.
"""

from __future__ import annotations

__version__ = "1.0.0"

__all__ = ["__version__"]
