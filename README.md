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
- [Login via Authentik (OAuth Proxy + DCR)](#login-via-authentik-oauth-proxy--dcr)
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
- 🔐 **Login via Authentik (OAuth Proxy + DCR)** — pengguna cukup **login di
  Authentik**; client id/secret **tidak perlu** diisi di Claude (Claude mendaftar
  otomatis lewat Dynamic Client Registration). Tersedia juga mode introspeksi
  (RFC 7662) sebagai kompatibilitas mundur.
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
├── auth.py          # pemilihan auth provider (OAuth Proxy / introspeksi)
├── auth_provider.py # AuthentikProvider (OAuth Proxy + DCR) — login via Authentik
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
| `OAUTH_CLIENT_ID` | – | Client ID OAuth provider Authentik (sisi server) |
| `OAUTH_CLIENT_SECRET` | – | Client Secret OAuth provider Authentik (sisi server) |
| `OAUTH_OIDC_CONFIG_URL` | – | OIDC discovery URL; domain & slug provider di-derive otomatis dari sini |
| `AUTHENTIK_OAUTH_DOMAIN` | – | (Opsional) URL publik Authentik bila tak memakai `OAUTH_OIDC_CONFIG_URL` |
| `AUTHENTIK_APP_SLUG` | – | (Opsional) slug provider bila tak memakai `OAUTH_OIDC_CONFIG_URL` |
| `AUTHENTIK_ALLOWED_USERNAMES` | – | Daftar username diizinkan (dipisah koma); kosong = semua user |
| `OAUTH_REQUIRED_SCOPES` | – | Scope login (dipisah spasi); default `openid profile email` |
| `MCP_BASE_URL` | – | URL publik server ini; **wajib** agar OAuth Proxy berfungsi |
| `OAUTH_INTROSPECTION_URL` | – | (Fallback) endpoint introspeksi (RFC 7662) bila OAuth Proxy tak lengkap |
| `OAUTH_CACHE_TTL` | – | TTL cache introspeksi (detik), `0` = nonaktif |
| `MCP_TRANSPORT` | – | `http` (default) atau `stdio` |
| `MCP_HOST` / `MCP_PORT` | – | Host/port saat transport http, default `0.0.0.0:8000` |
| `MCP_LOG_LEVEL` | – | `DEBUG`/`INFO`/`WARNING`/`ERROR` |

> **API Token Authentik** dibuat di: **Admin Interface → Directory → Tokens &
> App passwords → Create**. Token ini dipakai server untuk **semua** panggilan
> tool ke Authentik API.

> ℹ️ **Mode OAuth Proxy (login via Authentik)** aktif bila `OAUTH_CLIENT_ID`,
> `OAUTH_CLIENT_SECRET`, domain publik Authentik (dari `OAUTH_OIDC_CONFIG_URL`
> atau `AUTHENTIK_OAUTH_DOMAIN`), slug provider, dan `MCP_BASE_URL` terisi.
> Bila tak lengkap, server mundur ke introspeksi; bila itu pun kosong, server
> berjalan **tanpa autentikasi** (hanya untuk pengembangan lokal).

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

## Login via Authentik (OAuth Proxy + DCR)

MCP server ini dilindungi sehingga **hanya pengguna terautentikasi** yang dapat
mengaksesnya, menggunakan **Authentik** sebagai Identity Provider.

Pendekatan yang dipakai: **OAuth Proxy + Dynamic Client Registration**. MCP
server mengekspos endpoint OAuth-nya sendiri dan menerima pendaftaran client
otomatis dari Claude. Akibatnya, **pengguna tidak perlu memasukkan client
id/secret di Claude** — cukup **login di Authentik** saat menghubungkan
connector. `OAUTH_CLIENT_ID`/`OAUTH_CLIENT_SECRET` berada di sisi server
(`.env`), dibuat sekali oleh admin di Authentik.

> Catatan API: setelah login, panggilan tool ke Authentik API tetap memakai
> `AUTHENTIK_API_TOKEN` (server-side). Login Authentik berfungsi sebagai
> **gerbang akses** ke MCP server.

### 1. Buat OAuth2/OpenID Provider di Authentik

1. Masuk **Admin Interface → Applications → Providers → Create**.
2. Pilih tipe **OAuth2/OpenID Provider**.
3. Isi konfigurasi:
   - **Name**: mis. `authentik-mcp`.
   - **Authorization flow**: pilih flow consent/authorization yang sesuai
     (mis. `default-provider-authorization-explicit-consent`).
   - **Client type**: **Confidential**.
   - **Redirect URIs / Origins**: arahkan ke callback server MCP ini
     ```
     <MCP_BASE_URL>/auth/callback
     ```
     contoh: `https://mcp.yourdomain.com/auth/callback`
   - **Scopes**: aktifkan minimal `openid`, `profile`, `email`.
4. Buat juga **Application** (Applications → Applications → Create) dan tautkan ke
   provider di atas.

### 2. Ambil Client ID & Client Secret

Buka provider yang baru dibuat → bagian **Protocol settings**:

- **Client ID** dan **Client Secret** tertera di sana. Salin keduanya.
- **OIDC discovery URL** provider berbentuk:
  ```
  https://auth.yourdomain.com/application/o/authentik-mcp/.well-known/openid-configuration
  ```

### 3. Konfigurasi environment MCP server

Isi pada `.env`:

```bash
OAUTH_CLIENT_ID=<client-id-dari-authentik>
OAUTH_CLIENT_SECRET=<client-secret-dari-authentik>
# Domain publik & slug provider di-derive otomatis dari URL ini:
OAUTH_OIDC_CONFIG_URL=https://auth.yourdomain.com/application/o/authentik-mcp/.well-known/openid-configuration
# URL publik server MCP ini (wajib untuk OAuth Proxy):
MCP_BASE_URL=https://mcp.yourdomain.com
# Opsional: batasi user tertentu (kosong = semua user Authentik diizinkan):
AUTHENTIK_ALLOWED_USERNAMES=
```

Restart server. Pada log Anda akan melihat
`Autentikasi MCP aktif: AuthentikProvider (OAuth Proxy + DCR) ...`.

### 4. Tambahkan sebagai Custom Connector di Claude.ai

Di Claude.ai, buka **Settings → Connectors → Add custom connector**, lalu isi:

| Field | Nilai |
|---|---|
| **Name** | `Authentik` (bebas) |
| **Remote MCP server URL** | `https://mcp.yourdomain.com/mcp/` (URL publik server ini) |

Tidak ada kolom client id/secret yang perlu diisi — Claude mendaftar otomatis
(DCR). Saat menghubungkan, Anda akan diarahkan untuk **login di Authentik**.
Setelah login berhasil, connector aktif.

## Pengembangan & Test

Semua test memakai mock HTTP (`respx`) sehingga **tidak menyentuh Authentik
sungguhan**. Seluruh perintah berikut berjalan **di dalam Docker** — tidak ada
artifact (`.coverage`, `.pytest_cache`, dll.) yang dihasilkan di direktori lokal.

### Menggunakan Makefile (direkomendasikan)

Cara paling mudah dan identik dengan CI:

```bash
make check        # build → lint → test (simulasi penuh CI, satu perintah)
make build-test   # hanya build image test
make lint         # hanya ruff check + format check (butuh image terbangun)
make test         # hanya pytest (butuh image terbangun)
make help         # tampilkan semua target
```

### Perintah Docker manual

Ekuivalen dengan yang dijalankan Makefile, juga identik dengan CI:

```bash
# Build image test (identik CI: "Build test image")
docker build --target test -t authentik-mcp:test .

# Lint (identik CI: job "lint")
docker run --rm authentik-mcp:test ruff check src tests
docker run --rm authentik-mcp:test ruff format --check src tests

# Unit test (identik CI: "Run pytest")
docker run --rm authentik-mcp:test pytest
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
