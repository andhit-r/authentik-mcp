"""Tool MCP untuk mengelola Policy dan Policy Binding Authentik.

Mendaftarkan tool:
- Policy CRUD per tipe (expression, password, password_expiry, reputation,
  event_matcher) serta test policy.
- Policy Binding CRUD (list, get, create, update, delete).
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import AuthentikClient

# Pemetaan tipe policy -> path endpoint Authentik.
_POLICY_PATHS: dict[str, str] = {
    "expression": "/policies/expression/",
    "password": "/policies/password/",
    "password_expiry": "/policies/password_expiry/",
    "reputation": "/policies/reputation/",
    "event_matcher": "/policies/event_matcher/",
}


def _validate_policy_type(policy_type: str) -> str:
    """Validasi dan normalisasi policy_type; raise ValueError bila tidak dikenal."""
    key = policy_type.strip().lower()
    if key not in _POLICY_PATHS:
        valid = ", ".join(sorted(_POLICY_PATHS))
        raise ValueError(f"policy_type tidak valid: {policy_type!r}. Pilih salah satu: {valid}.")
    return key


def register(mcp: FastMCP, client: AuthentikClient) -> None:
    """Daftarkan seluruh tool domain Policy ke server MCP."""

    # ------------------------------------------------------------------
    # Policy CRUD
    # ------------------------------------------------------------------

    @mcp.tool(tags={"policies"})
    async def authentik_policy_list(
        search: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Daftar semua policy (lintas tipe) via ``/policies/all/``.

        Args:
            search: Kata kunci pencarian nama policy.
            page: Nomor halaman.
            page_size: Jumlah item per halaman.

        Returns:
            Objek paginasi berisi ``results`` (daftar policy beragam tipe).

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        params = {"search": search, "page": page, "page_size": page_size}
        return await client.get("/policies/all/", params=params)

    @mcp.tool(tags={"policies"})
    async def authentik_policy_get(
        policy_type: str,
        policy_uuid: str,
    ) -> dict[str, Any]:
        """Ambil detail satu policy sesuai tipenya.

        Args:
            policy_type: Tipe policy: ``expression``, ``password``,
                ``password_expiry``, ``reputation``, atau ``event_matcher``.
            policy_uuid: UUID policy.

        Returns:
            Objek policy lengkap sesuai tipe.

        Raises:
            ValueError: Bila ``policy_type`` tidak dikenal.
            AuthentikAPIError: 404 bila policy tidak ditemukan.
        """
        key = _validate_policy_type(policy_type)
        return await client.get(f"{_POLICY_PATHS[key]}{policy_uuid}/")

    @mcp.tool(tags={"policies"})
    async def authentik_policy_create(
        policy_type: str,
        name: str,
        expression: str | None = None,
        days: int | None = None,
        extra_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Buat policy baru.

        Field wajib bervariasi per tipe:

        - **expression**: ``expression`` wajib — kode Python yang dievaluasi.
        - **password_expiry**: ``days`` wajib — masa berlaku password (hari).
        - **password** / **reputation** / **event_matcher**: tidak ada field
          tambahan yang wajib; gunakan ``extra_config`` untuk konfigurasi
          spesifik (mis. ``length_min``, ``threshold``, ``action``).

        Args:
            policy_type: Tipe policy: ``expression``, ``password``,
                ``password_expiry``, ``reputation``, atau ``event_matcher``.
            name: Nama unik policy.
            expression: *(expression)* Kode Python policy.
            days: *(password_expiry)* Jumlah hari sebelum password kedaluwarsa.
            extra_config: Field opsional tambahan sesuai tipe
                (mis. ``length_min``, ``amount_digits``, ``check_ip``,
                ``threshold``, ``action``, ``execution_logging``).

        Returns:
            Objek policy yang baru dibuat (termasuk ``pk``).

        Raises:
            ValueError: Bila ``policy_type`` tidak dikenal atau field wajib
                per tipe tidak lengkap.
            AuthentikAPIError: 422 bila validasi Authentik gagal.
        """
        key = _validate_policy_type(policy_type)

        missing: list[str] = []
        if key == "expression" and expression is None:
            missing.append("expression")
        if key == "password_expiry" and days is None:
            missing.append("days")
        if missing:
            raise ValueError(f"Policy tipe {key!r} membutuhkan field: {', '.join(missing)}.")

        payload: dict[str, Any] = {"name": name}
        if expression is not None:
            payload["expression"] = expression
        if days is not None:
            payload["days"] = days
        if extra_config:
            payload.update(extra_config)

        return await client.post(_POLICY_PATHS[key], json=payload)

    @mcp.tool(tags={"policies"})
    async def authentik_policy_update(
        policy_type: str,
        policy_uuid: str,
        name: str | None = None,
        expression: str | None = None,
        days: int | None = None,
        extra_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Perbarui sebagian field policy (PATCH). Hanya field non-None yang dikirim.

        Args:
            policy_type: Tipe policy: ``expression``, ``password``,
                ``password_expiry``, ``reputation``, atau ``event_matcher``.
            policy_uuid: UUID policy.
            name: Nama baru.
            expression: *(expression)* Kode Python baru.
            days: *(password_expiry)* Jumlah hari baru.
            extra_config: Field opsional tambahan yang ingin diubah.

        Returns:
            Objek policy setelah diperbarui.

        Raises:
            ValueError: Bila ``policy_type`` tidak dikenal atau tidak ada
                field yang diberikan.
            AuthentikAPIError: 404 bila policy tidak ditemukan.
        """
        key = _validate_policy_type(policy_type)

        payload: dict[str, Any] = {}
        for field, value in {
            "name": name,
            "expression": expression,
            "days": days,
        }.items():
            if value is not None:
                payload[field] = value
        if extra_config:
            payload.update(extra_config)

        if not payload:
            raise ValueError("Tidak ada field yang diberikan untuk diperbarui.")

        return await client.patch(f"{_POLICY_PATHS[key]}{policy_uuid}/", json=payload)

    @mcp.tool(tags={"policies"})
    async def authentik_policy_delete(policy_uuid: str) -> dict[str, str]:
        """Hapus policy secara permanen via endpoint generik ``/policies/all/``.

        Args:
            policy_uuid: UUID policy (berlaku untuk semua tipe).

        Returns:
            Konfirmasi penghapusan.

        Raises:
            AuthentikAPIError: 404 bila policy tidak ditemukan.
        """
        await client.delete(f"/policies/all/{policy_uuid}/")
        return {"status": "deleted", "policy_uuid": policy_uuid}

    @mcp.tool(tags={"policies"})
    async def authentik_policy_test(
        policy_uuid: str,
        user_id: int,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Uji policy terhadap user tertentu.

        Args:
            policy_uuid: UUID policy yang akan diuji.
            user_id: pk numerik user sebagai subjek pengujian.
            context: Konteks tambahan yang diteruskan ke policy saat evaluasi
                (mis. ``{"flow_plan": {...}}``).

        Returns:
            Hasil evaluasi policy berisi ``passing`` (bool) dan ``messages``
            (list pesan).

        Raises:
            AuthentikAPIError: 404 bila policy tidak ditemukan.
        """
        payload: dict[str, Any] = {"user": user_id}
        if context is not None:
            payload["context"] = context
        return await client.post(f"/policies/all/{policy_uuid}/test/", json=payload)

    # ------------------------------------------------------------------
    # Policy Binding CRUD
    # ------------------------------------------------------------------

    @mcp.tool(tags={"policies"})
    async def authentik_policy_binding_list(
        target: str | None = None,
        policy: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Daftar policy binding dengan filter opsional.

        Args:
            target: UUID objek target (aplikasi, flow, dll.) untuk difilter.
            policy: UUID policy untuk difilter.
            page: Nomor halaman.
            page_size: Jumlah item per halaman.

        Returns:
            Objek paginasi berisi ``results`` (daftar policy binding).

        Raises:
            AuthentikAPIError: Bila request gagal.
        """
        params = {"target": target, "policy": policy, "page": page, "page_size": page_size}
        return await client.get("/policies/bindings/", params=params)

    @mcp.tool(tags={"policies"})
    async def authentik_policy_binding_get(binding_uuid: str) -> dict[str, Any]:
        """Ambil detail satu policy binding.

        Args:
            binding_uuid: UUID policy binding.

        Returns:
            Objek policy binding lengkap.

        Raises:
            AuthentikAPIError: 404 bila binding tidak ditemukan.
        """
        return await client.get(f"/policies/bindings/{binding_uuid}/")

    @mcp.tool(tags={"policies"})
    async def authentik_policy_binding_create(
        target: str,
        order: int,
        policy: str | None = None,
        group: str | None = None,
        user: int | None = None,
        negate: bool = False,
        enabled: bool = True,
        timeout: int = 30,
        failure_result: bool = False,
    ) -> dict[str, Any]:
        """Buat policy binding baru (kaitkan policy/grup/user ke objek target).

        Tepat satu dari ``policy``, ``group``, atau ``user`` harus diisi.

        Args:
            target: UUID objek yang ingin dilindungi (aplikasi, flow, dll.).
            order: Urutan evaluasi binding (angka lebih kecil dievaluasi lebih dulu).
            policy: UUID policy yang diikat (opsional, pilih salah satu).
            group: UUID grup yang diikat (opsional, pilih salah satu).
            user: pk numerik user yang diikat (opsional, pilih salah satu).
            negate: Balik hasil evaluasi policy (default False).
            enabled: Aktifkan binding (default True).
            timeout: Waktu tunggu evaluasi dalam detik (default 30).
            failure_result: Hasil bila evaluasi gagal/timeout (default False).

        Returns:
            Objek policy binding yang baru dibuat (termasuk ``pk``).

        Raises:
            ValueError: Bila tidak ada satu pun dari policy/group/user yang diisi.
            AuthentikAPIError: 422 bila validasi Authentik gagal.
        """
        if policy is None and group is None and user is None:
            raise ValueError("Salah satu dari 'policy', 'group', atau 'user' harus diisi.")

        payload: dict[str, Any] = {
            "target": target,
            "order": order,
            "negate": negate,
            "enabled": enabled,
            "timeout": timeout,
            "failure_result": failure_result,
        }
        if policy is not None:
            payload["policy"] = policy
        if group is not None:
            payload["group"] = group
        if user is not None:
            payload["user"] = user

        return await client.post("/policies/bindings/", json=payload)

    @mcp.tool(tags={"policies"})
    async def authentik_policy_binding_update(
        binding_uuid: str,
        order: int | None = None,
        policy: str | None = None,
        group: str | None = None,
        user: int | None = None,
        negate: bool | None = None,
        enabled: bool | None = None,
        timeout: int | None = None,
        failure_result: bool | None = None,
    ) -> dict[str, Any]:
        """Perbarui sebagian field policy binding (PATCH).

        Args:
            binding_uuid: UUID policy binding.
            order: Urutan evaluasi baru.
            policy: UUID policy baru.
            group: UUID grup baru.
            user: pk numerik user baru.
            negate: Nilai negate baru.
            enabled: Status aktif baru.
            timeout: Timeout baru (detik).
            failure_result: Hasil kegagalan baru.

        Returns:
            Objek policy binding setelah diperbarui.

        Raises:
            ValueError: Bila tidak ada field yang diberikan.
            AuthentikAPIError: 404 bila binding tidak ditemukan.
        """
        payload: dict[str, Any] = {}
        for field, value in {
            "order": order,
            "policy": policy,
            "group": group,
            "user": user,
            "negate": negate,
            "enabled": enabled,
            "timeout": timeout,
            "failure_result": failure_result,
        }.items():
            if value is not None:
                payload[field] = value

        if not payload:
            raise ValueError("Tidak ada field yang diberikan untuk diperbarui.")

        return await client.patch(f"/policies/bindings/{binding_uuid}/", json=payload)

    @mcp.tool(tags={"policies"})
    async def authentik_policy_binding_delete(binding_uuid: str) -> dict[str, str]:
        """Hapus policy binding secara permanen.

        Args:
            binding_uuid: UUID policy binding.

        Returns:
            Konfirmasi penghapusan.

        Raises:
            AuthentikAPIError: 404 bila binding tidak ditemukan.
        """
        await client.delete(f"/policies/bindings/{binding_uuid}/")
        return {"status": "deleted", "binding_uuid": binding_uuid}
