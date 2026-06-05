"""Paket berisi seluruh tool MCP, dikelompokkan per domain Authentik.

Setiap submodul mengekspos fungsi ``register(mcp, client)`` yang mendaftarkan
tool-tool domainnya ke instance FastMCP. Fungsi :func:`register_all` di sini
memanggil seluruh ``register`` tersebut.
"""

from __future__ import annotations

from fastmcp import FastMCP

from ..client import AuthentikClient
from . import (
    applications,
    crypto,
    events,
    flows,
    groups,
    outposts,
    policies,
    property_mappings,
    providers,
    roles,
    system,
    tokens,
    users,
)

# Urutan modul menentukan urutan registrasi (dan urutan tampil di dokumentasi).
_MODULES = [
    users,
    groups,
    roles,
    applications,
    providers,
    policies,
    property_mappings,
    crypto,
    tokens,
    events,
    flows,
    outposts,
    system,
]


def register_all(mcp: FastMCP, client: AuthentikClient) -> None:
    """Daftarkan seluruh tool dari setiap domain ke server MCP.

    Args:
        mcp: Instance FastMCP tempat tool didaftarkan.
        client: Klien Authentik bersama yang dipakai semua tool.
    """
    for module in _MODULES:
        module.register(mcp, client)
