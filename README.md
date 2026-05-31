# authentik-mcp

MCP (Model Context Protocol) server untuk **mengelola [Authentik](https://goauthentik.io/)
melalui REST API**, dibangun dengan [FastMCP](https://github.com/jlowin/fastmcp).

Server ini mengekspos tool-tool untuk mengelola users, groups, applications,
providers, tokens, events, flows, property mappings, dan outposts pada instance
Authentik Anda — siap dipakai dari Claude.ai atau klien MCP lain.

---

## Daftar Isi

- [Fitur](#fitur)
- [Arsitektur](#arsitektur)
- [Tool yang Tersedia](#tool-yang-tersedia)
- [Konfigurasi](#konfigurasi)
- [Menjalankan](#menjalankan)
  - [Lokal (Python)](#lokal-python)
  - [Docker](#docker)
- [Dokumentasi API (Swagger)](#dokumentasi-api-swagger)
- [Proteksi Akses MCP via OAuth (Authentik sebagai IdP)](#proteksi-akses-mcp-via-oauth-authentik-sebagai-idp)
  - [1. Buat OAuth2/OpenID Provider di Authentik](#1-buat-oauth2openid-provider-di-authentik)
  - [2. Ambil Client ID & Client Secret](#2-ambil-client-id--client-secret)
  - [3. Konfigurasi environment MCP server](#3-konfigurasi-environment-mcp-server)
  - [4. Tambahkan sebagai Custom Connector di Claude.ai](#4-tambahkan-sebagai-custom-connector-di-claudeai)
- [Pengembangan & Test](#pengembangan--test)
- [Rilis & Tagging](#rilis--tagging)
- [Lisensi](#lisensi)

---

## Fitur

- 🔧 **39 tool** terorganisir per domain Authentik dengan penamaan konsisten
  (`authentik_<domain>_<aksi>`).
- 🔐 **Proteksi OAuth bawaan** — validasi Bearer token client lewat OAuth 2.0
  Token Introspection (RFC 7662) ke Authentik (`/application/o/introspect/`).
- 🧰 **Penanganan error eksplisit** untuk 401/403/404/422/500 dengan pesan
  informatif.
- 📖 **Swagger UI** untuk meninjau seluruh tool beserta skema parameternya.
- 🐳 **Docker-first** — image runtime ramping + stage test untuk CI.
- ✅ **Unit test** ter-mock penuh (tidak pernah menyentuh Authentik sungguhan).

## Arsitektur

```
src/authentik_mcp/
├── config.py        # konfigurasi dari environment (pydantic-settings)
├── client.py        # klien HTTP async ke Authentik + penanganan error
├── auth.py          # verifier OAuth introspection (proteksi MCP)
├── docs.py          # rute Swagger/OpenAPI & /health
├── server.py        # perakitan FastMCP + registrasi semua tool
├── logging.py       # logging terpusat
└── tools/           # implementasi tool per domain
    ├── users.py            applications.py     tokens.py        flows.py
    ├── groups.py           providers.py        events.py        property_mappings.py
    └── outposts.py
```

Semua tool memakai satu `AuthentikClient` bersama (koneksi HTTP di-pool).
Konfigurasi tidak pernah di-hardcode — seluruhnya dari environment variable.

## Tool yang Tersedia

| Domain | Tool |
|---|---|
| **Users** | `authentik_user_list`, `authentik_user_get`, `authentik_user_create`, `authentik_user_update`, `authentik_user_delete`, `authentik_user_set_password`, `authentik_user_activate`, `authentik_user_deactivate` |
| **Groups** | `authentik_group_list`, `authentik_group_get`, `authentik_group_create`, `authentik_group_update`, `authentik_group_delete`, `authentik_group_add_member`, `authentik_group_remove_member` |
| **Applications** | `authentik_application_list`, `authentik_application_get`, `authentik_application_create`, `authentik_application_update`, `authentik_application_delete` |
| **Providers** | `authentik_provider_list`, `authentik_provider_get` (OAuth2/LDAP/SAML/Proxy) |
| **Tokens** | `authentik_token_list`, `authentik_token_get`, `authentik_token_create`, `authentik_token_revoke` |
| **Events/Logs** | `authentik_event_list`, `authentik_event_get`, `authentik_event_filter_by_action`, `authentik_event_filter_by_user` |
| **Flows** | `authentik_flow_list`, `authentik_flow_get`, `authentik_flow_execute` |
| **Property Mappings** | `authentik_property_mapping_list`, `authentik_property_mapping_get` |
| **Outposts** | `authentik_outpost_list`, `authentik_outpost_get`, `authentik_outpost_update`, `authentik_outpost_health` |

Setiap tool memiliki docstring lengkap (parameter, return, error). Tinjau detail
skema lewat [Swagger UI](#dokumentasi-api-swagger).

## Konfigurasi

Salin `.env.example` menjadi `.env` lalu isi nilainya. Variabel utama:

| Variable | Wajib | Keterangan |
|---|---|---|
| `AUTHENTIK_URL` | ✅ | URL dasar Authentik, mis. `https://auth.yourdomain.com` |
| `AUTHENTIK_API_TOKEN` | ✅ | API Token Authentik (dikirim sebagai `Authorization: Bearer`) |
| `AUTHENTIK_TIMEOUT` | – | Timeout request (detik), default `30` |
| `AUTHENTIK_VERIFY_SSL` | – | Verifikasi TLS Authentik, default `true` |
| `OAUTH_INTROSPECTION_URL` | – | Endpoint introspeksi, mis. `https://auth.yourdomain.com/application/o/introspect/` |
| `OAUTH_CLIENT_ID` | – | Client ID OAuth untuk proteksi MCP |
| `OAUTH_CLIENT_SECRET` | – | Client Secret OAuth untuk proteksi MCP |
| `OAUTH_REQUIRED_SCOPES` | – | Scope wajib (dipisah spasi) |
| `OAUTH_CACHE_TTL` | – | TTL cache introspeksi (detik), `0` = nonaktif |
| `MCP_TRANSPORT` | – | `http` (default) atau `stdio` |
| `MCP_HOST` / `MCP_PORT` | – | Host/port saat transport http, default `0.0.0.0:8000` |
| `MCP_LOG_LEVEL` | – | `DEBUG`/`INFO`/`WARNING`/`ERROR` |

> **API Token Authentik** dibuat di: **Admin Interface → Directory → Tokens &
> App passwords → Create**. Gunakan token milik akun dengan hak yang sesuai.

> ⚠️ Bila variabel `OAUTH_*` dikosongkan, MCP server berjalan **tanpa
> autentikasi** — hanya untuk pengembangan lokal, jangan dipakai di produksi.

## Menjalankan

### Lokal (Python)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env   # lalu isi AUTHENTIK_URL & AUTHENTIK_API_TOKEN
authentik-mcp          # atau: python -m authentik_mcp
```

Server HTTP akan tersedia di `http://localhost:8000` (endpoint MCP di `/mcp/`).

### Docker

```bash
# Build image runtime
docker build --target runtime -t authentik-mcp:latest .

# Jalankan dengan file .env
docker run --rm -p 8000:8000 --env-file .env authentik-mcp:latest
```

Image siap pakai juga tersedia di GHCR setelah rilis:

```bash
docker run --rm -p 8000:8000 --env-file .env ghcr.io/andhit-r/authentik-mcp:latest
```

## Dokumentasi API (Swagger)

Saat transport `http`, server menyediakan:

- `GET /docs` — **Swagger UI** yang mendokumentasikan seluruh tool MCP beserta
  skema parameternya.
- `GET /openapi.json` — dokumen OpenAPI 3.1 (dihasilkan otomatis dari tool).
- `GET /health` — health check.

> Catatan: tool MCP dipanggil melalui protokol MCP pada `/mcp/`. Dokumen OpenAPI
> bersifat deskriptif untuk memudahkan peninjauan skema tiap tool.

## Proteksi Akses MCP via OAuth (Authentik sebagai IdP)

MCP server ini dapat dilindungi sehingga **hanya pengguna terautentikasi** yang
dapat mengaksesnya, menggunakan **Authentik sendiri** sebagai Identity Provider.

Pendekatan yang dipakai: **Bearer token validation bawaan FastMCP**. Saat
client (mis. Claude.ai) memanggil MCP server, token yang dibawanya divalidasi
secara real-time melalui **OAuth 2.0 Token Introspection (RFC 7662)** ke endpoint
`/application/o/introspect/` milik Authentik.

### 1. Buat OAuth2/OpenID Provider di Authentik

1. Masuk **Admin Interface → Applications → Providers → Create**.
2. Pilih tipe **OAuth2/OpenID Provider**.
3. Isi konfigurasi:
   - **Name**: mis. `authentik-mcp`.
   - **Authorization flow**: pilih flow consent/authorization yang sesuai
     (mis. `default-provider-authorization-explicit-consent`).
   - **Client type**: **Confidential**.
   - **Redirect URIs / Origins**: tambahkan
     ```
     https://claude.ai/oauth/callback
     ```
   - **Scopes**: aktifkan minimal `openid`, `profile`, `email` (sesuaikan dengan
     `OAUTH_REQUIRED_SCOPES` bila Anda mewajibkan scope tertentu).
4. Buat juga **Application** (Applications → Applications → Create) dan tautkan ke
   provider di atas agar muncul di portal pengguna.

### 2. Ambil Client ID & Client Secret

Buka provider yang baru dibuat → bagian **Protocol settings**:

- **Client ID** dan **Client Secret** tertera di sana. Salin keduanya.
- **Token introspection URL** Authentik berbentuk:
  ```
  https://auth.yourdomain.com/application/o/introspect/
  ```

### 3. Konfigurasi environment MCP server

Isi pada `.env`:

```bash
OAUTH_INTROSPECTION_URL=https://auth.yourdomain.com/application/o/introspect/
OAUTH_CLIENT_ID=<client-id-dari-authentik>
OAUTH_CLIENT_SECRET=<client-secret-dari-authentik>
# Opsional, wajibkan scope tertentu:
OAUTH_REQUIRED_SCOPES=openid profile
```

Restart server. Pada log Anda akan melihat `Autentikasi MCP aktif: introspeksi
token ke ...`.

### 4. Tambahkan sebagai Custom Connector di Claude.ai

Di Claude.ai, buka **Settings → Connectors → Add custom connector**, lalu isi:

| Field | Nilai |
|---|---|
| **Name** | `Authentik` (bebas) |
| **Remote MCP server URL** | `https://mcp.yourdomain.com/mcp/` (URL publik server ini) |
| **OAuth Client ID** | Client ID dari Authentik (langkah 2) |
| **OAuth Client Secret** | Client Secret dari Authentik (langkah 2) |

Redirect URI yang dipakai Claude.ai adalah `https://claude.ai/oauth/callback`
— pastikan sudah terdaftar di provider Authentik (langkah 1). Setelah connector
ditambahkan, Claude.ai akan menjalankan alur OAuth ke Authentik; token hasilnya
divalidasi server ini via introspeksi setiap request.

## Pengembangan & Test

Semua test memakai mock HTTP (`respx`) sehingga **tidak menyentuh Authentik
sungguhan**. Jalankan via Docker (build dulu, lalu test di dalam image):

```bash
# Build image test
docker build --target test -t authentik-mcp:test .

# Linter
docker run --rm authentik-mcp:test ruff check src tests
docker run --rm authentik-mcp:test ruff format --check src tests

# Unit test
docker run --rm authentik-mcp:test pytest
```

Atau langsung di lingkungan lokal:

```bash
pip install -e ".[dev]"
ruff check src tests
pytest
```

## Rilis & Tagging

Menggunakan **Semantic Versioning** (`MAJOR.MINOR.PATCH`), format tag `vX.Y.Z`.

| Tipe perubahan | Naikkan |
|---|---|
| Breaking change pada tool/API | `MAJOR` |
| Fitur baru (tool/resource/endpoint) | `MINOR` |
| Bug fix, refactor, update dependency | `PATCH` |
| Dokumentasi/konfigurasi saja | `PATCH` |

Mendorong tag `vX.Y.Z` ke `master` memicu workflow **Release**: menjalankan
ulang test, membuat **GitHub Release**, lalu build & publish image ke
`ghcr.io/<owner>/<repo>`.

## Lisensi

MIT — lihat berkas `LICENSE` (bila tersedia) atau metadata lisensi pada `pyproject.toml`.
