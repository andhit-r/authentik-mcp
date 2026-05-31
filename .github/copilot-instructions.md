# Copilot Instructions — authentik-mcp

Panduan ini membantu GitHub Copilot (dan asisten AI lain) memahami dan
berkontribusi pada repositori ini secara konsisten.

## Ringkasan Proyek

`authentik-mcp` adalah **MCP server** (Model Context Protocol) yang mengelola
**Authentik** melalui REST API-nya, dibangun di atas **FastMCP** (Python).
Server mengekspos tool per domain Authentik dan dapat dilindungi dengan OAuth
(Authentik sebagai Identity Provider) via token introspection (RFC 7662).

## Aturan Wajib (selalu diikuti)

1. **Inspeksi versi package sebelum menulis kode.** Jangan berasumsi tentang
   API pihak ketiga. Jalankan mis. `pip show fastmcp`, `pip show httpx`, dan
   baca source/docstring yang relevan terlebih dahulu. Versi yang menjadi acuan
   saat ini: **fastmcp 3.x**, **httpx 0.28.x**, **pydantic 2.x**.
2. **Jangan hardcode credential atau URL.** Semua konfigurasi lewat environment
   variable melalui `src/authentik_mcp/config.py` (pydantic-settings).
3. **Selalu tulis/perbarui docstring** setiap menambah atau mengubah kode, agar
   AI dan manusia dapat memahaminya di kemudian hari. Gaya docstring: Google
   style (Args/Returns/Raises), berbahasa Indonesia (konsisten dengan kode yang
   ada).
4. **Jalankan unit test via Docker** setiap ada perubahan: build image dulu,
   lalu jalankan test memakai image tersebut (lihat bagian Test).

## Struktur Direktori

```
src/authentik_mcp/
  config.py     -> Settings (env), get_settings()
  client.py     -> AuthentikClient (httpx async) + AuthentikAPIError
  auth.py       -> build_token_verifier() (IntrospectionTokenVerifier)
  docs.py       -> rute /docs, /openapi.json, /health
  server.py     -> create_server(), run()
  logging.py    -> configure_logging(), get_logger()
  tools/        -> satu modul per domain; tiap modul punya register(mcp, client)
tests/          -> pytest + respx (mock HTTP), terpisah dari source
```

## Konvensi Kode

- **Penamaan tool**: `authentik_<domain>_<aksi>`, mis. `authentik_user_list`,
  `authentik_group_create`. Konsisten dan deskriptif.
- **Registrasi tool**: setiap modul di `tools/` mengekspos
  `def register(mcp: FastMCP, client: AuthentikClient) -> None` dan
  mendefinisikan tool dengan dekorator `@mcp.tool(tags={"<domain>"})`. Daftarkan
  modul baru di `tools/__init__.py` (`_MODULES`).
- **Akses HTTP**: selalu lewat `AuthentikClient` (`client.get/post/patch/delete`).
  Jangan memanggil `httpx` langsung dari modul tool.
- **Penanganan error**: error HTTP Authentik diterjemahkan menjadi
  `AuthentikAPIError` dengan pesan informatif per status (401/403/404/422/500)
  di `client.py`. Untuk validasi input di level tool, lempar `ValueError`.
- **Path API Authentik**: relatif terhadap `/api/v3` (base URL sudah mencakup
  prefix tersebut), mis. `"/core/users/"`.
- **Tipe & gaya**: gunakan `from __future__ import annotations`, type hints
  lengkap, dan patuhi `ruff` (lint + format).

## Menambah Tool Baru (langkah)

1. Tentukan endpoint Authentik yang tepat (cek dokumentasi/Swagger Authentik).
2. Tambah fungsi async di modul domain terkait (atau buat modul baru +
   daftarkan di `tools/__init__.py`).
3. Beri nama `authentik_<domain>_<aksi>`, tambahkan docstring Args/Returns/Raises.
4. Tulis unit test ber-mock (respx) untuk happy path + minimal satu jalur error.
5. Jalankan lint & test via Docker. Pastikan hijau.

## Test (wajib via Docker)

```bash
docker build --target test -t authentik-mcp:test .
docker run --rm authentik-mcp:test ruff check src tests
docker run --rm authentik-mcp:test ruff format --check src tests
docker run --rm authentik-mcp:test pytest
```

- Semua HTTP call ke Authentik **harus di-mock** (`respx`). Jangan pernah
  menghubungi instance Authentik sungguhan dalam test.
- Cakupan minimal: happy path, error HTTP (401/404/500), dan validasi input.

## Git & Rilis

- Branch utama: **master**. Gunakan **GitHub CLI (`gh`)** untuk PR/release.
- **Commit message dalam Bahasa Indonesia**, informatif (jelaskan perubahan).
- Diminta commit → langsung commit. Diminta push ke master → push ke `master`.
  Diminta push tanpa merge → push ke branch lain lalu `gh pr create` ke master.
- **Semantic Versioning** `MAJOR.MINOR.PATCH`, tag `vX.Y.Z`:
  - Breaking change tool/API → MAJOR
  - Fitur baru (tool/resource/endpoint) → MINOR
  - Bug fix/refactor/update dependency → PATCH
  - Dokumentasi/konfigurasi saja → PATCH
- Tag `vX.Y.Z` memicu workflow Release (GitHub Release + image GHCR).

## Yang TIDAK Boleh

- Menaruh secret/token/URL nyata di kode, test, atau contoh commit.
- Memanggil Authentik sungguhan dari unit test.
- Mengubah perilaku tool tanpa memperbarui docstring dan test terkait.
- Menambah dependency berat tanpa alasan jelas; selaras dengan rentang versi di
  `pyproject.toml`.
