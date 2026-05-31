# syntax=docker/dockerfile:1
# ============================================================================
# Image untuk authentik-mcp.
# Multi-stage agar image akhir ramping namun tetap bisa menjalankan test
# (dev dependencies dipasang di stage terpisah).
# ============================================================================

FROM python:3.12-slim AS base

# Variabel lingkungan Python yang umum untuk container.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Salin metadata proyek lebih dulu agar layer dependency dapat di-cache.
COPY pyproject.toml README.md ./
COPY src ./src

# ---------------------------------------------------------------------------
# Stage test: berisi dependency pengembangan (pytest, ruff, respx, dll).
# Dipakai di CI untuk menjalankan lint dan unit test.
#   docker build --target test -t authentik-mcp:test .
#   docker run --rm authentik-mcp:test
# ---------------------------------------------------------------------------
FROM base AS test

RUN pip install --no-cache-dir ".[dev]"
COPY tests ./tests
# Perintah default stage test: jalankan seluruh unit test.
CMD ["pytest"]

# ---------------------------------------------------------------------------
# Stage runtime: image produksi yang ramping, hanya dependency runtime.
# ---------------------------------------------------------------------------
FROM base AS runtime

RUN pip install --no-cache-dir "."

# Jalankan sebagai user non-root demi keamanan.
RUN useradd --create-home --uid 10001 appuser
USER appuser

# Port default transport HTTP MCP.
EXPOSE 8000

# Healthcheck memanggil endpoint /health yang disediakan server.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os,urllib.request,sys; \
        port=os.environ.get('MCP_PORT','8000'); \
        urllib.request.urlopen(f'http://127.0.0.1:{port}/health'); sys.exit(0)" \
        || exit 1

# Jalankan server MCP.
CMD ["python", "-m", "authentik_mcp"]
