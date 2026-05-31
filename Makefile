# =============================================================================
# Makefile untuk authentik-mcp
#
# Seluruh target menjalankan perintah di dalam Docker sehingga tidak ada
# artifact (coverage, .pytest_cache, dll.) yang dihasilkan di direktori lokal.
# Perintah dan image yang dipakai identik dengan .github/workflows/ci.yml.
#
# Penggunaan umum:
#   make check        # simulasi penuh CI: build → lint → test
#   make build-test   # hanya build image test
#   make lint         # hanya lint (butuh image sudah terbangun)
#   make test         # hanya test (butuh image sudah terbangun)
# =============================================================================

IMAGE_TEST := authentik-mcp:test

.PHONY: help build-test lint test check

# ---------------------------------------------------------------------------
# help: tampilkan daftar target yang tersedia
# ---------------------------------------------------------------------------
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# build-test: bangun Docker image stage "test"
#   Identik dengan langkah "Build test image" di CI (job: test).
# ---------------------------------------------------------------------------
build-test: ## Bangun Docker image untuk test (stage: test)
	docker build --target test -t $(IMAGE_TEST) .

# ---------------------------------------------------------------------------
# lint: jalankan ruff check + ruff format --check di dalam container
#   Identik dengan job "lint" di CI, namun dijalankan dalam image yang sama
#   agar versi ruff konsisten dan tidak menghasilkan artifact lokal.
#   Butuh image sudah terbangun (jalankan `make build-test` terlebih dahulu).
# ---------------------------------------------------------------------------
lint: ## Jalankan ruff check + format check di dalam Docker
	docker run --rm $(IMAGE_TEST) ruff check src tests
	docker run --rm $(IMAGE_TEST) ruff format --check src tests

# ---------------------------------------------------------------------------
# test: jalankan pytest di dalam container
#   Identik dengan langkah "Run pytest" di CI (job: test).
#   Butuh image sudah terbangun (jalankan `make build-test` terlebih dahulu).
# ---------------------------------------------------------------------------
test: ## Jalankan pytest di dalam Docker
	docker run --rm $(IMAGE_TEST) pytest

# ---------------------------------------------------------------------------
# check: simulasi penuh CI — build → lint → test (satu build, tanpa artifact)
#   Menggabungkan seluruh job CI dalam satu perintah lokal.
# ---------------------------------------------------------------------------
check: build-test ## Simulasi penuh CI: build → lint → test
	docker run --rm $(IMAGE_TEST) ruff check src tests
	docker run --rm $(IMAGE_TEST) ruff format --check src tests
	docker run --rm $(IMAGE_TEST) pytest
