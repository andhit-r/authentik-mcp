# Changelog

Semua perubahan penting pada proyek ini didokumentasikan di sini.

Format mengikuti [Keep a Changelog](https://keepachangelog.com/id/1.1.0/)
dan proyek ini menggunakan [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [1.10.0] - 2026-11-07

### Ditambahkan
- Tool tulis: `authentik_source_oauth_create`/`_update`/`_delete`, `authentik_stage_identification_update`, `authentik_flow_binding_create`/`_update`/`_delete`. Create source bawaan `user_matching_mode=identifier` tanpa enrollment flow; `consumer_secret` tidak pernah muncul di keluaran/error.
- Tool baca-saja stage, binding flow-stage, dan device MFA: `authentik_stage_list`, `authentik_stage_identification_get`, `authentik_stage_authenticator_validate_get`, `authentik_flow_binding_list`, `authentik_flow_binding_get`, `authentik_authenticator_admin_list`.
- Tool baca-saja source OAuth: `authentik_source_list`, `authentik_source_oauth_list`, `authentik_source_oauth_get`, `authentik_source_connection_list` (`consumer_secret` dibuang dari keluaran).
- Parameter `superuser_full_list` (bawaan `False`) pada `authentik_application_list` untuk daftar aplikasi lengkap.

---

## [1.9.0] - 2026-11-03

### Ditambahkan
- **Mode auth API key statis** — env `MCP_API_KEY` (Bearer) lewat `BearerApiKeyVerifier` (perbandingan waktu konstan `hmac.compare_digest`). Dapat dipakai sendiri atau digabung dengan OAuth lewat `MultiAuth`. Lihat Andhit-s-To-Do-List/shared-infra-support#53.

### Diubah
- **Transport `http` gagal-tertutup** — `run()` melempar `ValueError` (exit code 1) bila tidak ada auth sama sekali (tanpa `MCP_API_KEY` maupun OAuth), sehingga server tidak lagi berjalan tanpa autentikasi. `/health` tetap terbuka; `stdio` tidak berubah.

---

## [1.8.0] - 2026-11-02

### Diubah
- **Rilis image multi-arch** — job `docker-image` di `release.yml` dimigrasi ke reusable workflow `andhit-r/release-docker-image-ghcr` (`ghcr.yml@v2`) dengan `platforms: linux/amd64,linux/arm64`, agar image GHCR dapat berjalan di node SBC ARM (Docker Swarm). Lihat Andhit-s-To-Do-List/shared-infra-support#23.
- Tag image `:<major>` (mis. `:1`) dan cache `type=gha` tidak lagi dihasilkan; tag `{{version}}`, `{{major}}.{{minor}}`, dan `latest` tetap.

---

## [1.7.0] - 2026-06-21

### Ditambahkan
- **Flow CRUD** — tool `authentik_flow_create`, `authentik_flow_update`, dan `authentik_flow_delete` untuk membuat, memperbarui, dan menghapus flow Authentik. Melengkapi tool `list`, `get`, dan `execute` yang sudah ada sebelumnya.
- Test untuk ketiga tool baru (happy path create, update, update tanpa field, delete) di `test_other_tools.py`.

---

## [1.6.0] - 2026-06-05

### Ditambahkan
- **Modul `crypto`** — tool CRUD lengkap untuk certificate-key pair (`authentik_certificate_list/get/create/generate/update/delete/view/view_private_key`).
- **Modul `system`** — tool admin & informasi sistem (`authentik_system_info`, `authentik_system_version`, `authentik_system_apps`, `authentik_system_models`, `authentik_system_settings_get`, `authentik_system_settings_update`, `authentik_system_version_history`).
- **Provider** — dukungan 6 tipe provider baru: `scim`, `rac`, `ssf`, `wsfed`, `google_workspace`, `microsoft_entra` (total 11 tipe dari 5 sebelumnya).
- **Policy** — 3 tipe policy baru: `dummy`, `geoip` (field wajib `countries`), `unique_password`.
- **Property Mapping** — CRUD + test penuh untuk 15 tipe (provider: scope/saml/scim/rac/radius/google_workspace/microsoft_entra; source: ldap/oauth/plex/saml/scim/kerberos/telegram; notification).
- Test coverage untuk seluruh fitur baru (test_crypto.py, test_system.py, test_property_mappings.py).

### Diubah
- `providers.py` — validasi field wajib per tipe digeneralisasi ke tabel `_PROVIDER_REQUIRED`; `authorization_flow`/`invalidation_flow` kini opsional (tipe scim/ssf/google_workspace/microsoft_entra tidak membutuhkannya).
- `policies.py` — validasi required direfaktor ke tabel `_POLICY_REQUIRED`; tambah parameter `countries`.
- `property_mappings.py` — diubah dari read-only menjadi CRUD penuh + test endpoint.
- README diperbarui dengan tabel tool terkini dan pohon direktori modul baru.

---

## [1.5.0] - 2026-05-31

### Ditambahkan
- Modul `roles` — tool CRUD Roles dan RBAC (permission list, assign/unassign role & user permission).

---

## [1.4.0] - 2026-05-31

### Ditambahkan
- Modul `providers` — CRUD provider per tipe (OAuth2, LDAP, SAML, Proxy, Radius).

---

## [1.3.0] - 2026-05-31

### Ditambahkan
- Modul `policies` — CRUD policy per tipe dan policy binding.
- CLAUDE.md symlink ke root.

---

## [1.0.0] - 2026-05-01

### Ditambahkan
- Rilis awal MCP server Authentik: users, groups, applications, tokens, events, flows, property mappings, outposts.
- Autentikasi OAuth2 via token introspection (RFC 7662).
- Dokumentasi API (Swagger/OpenAPI) via `/docs`.
