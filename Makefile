.PHONY: help clean dev-install install test test-cov lint format typecheck security check build version publish publish-test publish-manual release bump-patch bump-minor bump-major

# Auto-discover packages
PACKAGES := $(wildcard packages/*)
PACKAGE_NAMES := $(notdir $(PACKAGES))

# Detect if 'uv' is available
UV := $(shell command -v uv 2> /dev/null)

help:
	@echo "chuk-virtual-experts - Monorepo Management"
	@echo ""
	@echo "Packages: $(PACKAGE_NAMES)"
	@echo ""
	@echo "Available targets (run across ALL packages):"
	@echo "  help              Show this help message"
	@echo ""
	@echo "Workspace targets:"
	@echo "  sync              Sync uv workspace (install all packages)"
	@echo "  dev-install       Install all packages in editable mode with dev deps"
	@echo "  install           Install all packages"
	@echo ""
	@echo "Quality targets:"
	@echo "  test              Run tests for all packages"
	@echo "  test-cov          Run tests with coverage for all packages"
	@echo "  lint              Run linting on all packages"
	@echo "  format            Auto-format all packages"
	@echo "  typecheck         Run type checking on all packages"
	@echo "  security          Run security checks on all packages"
	@echo "  check             Run all checks (lint, typecheck, security, test)"
	@echo ""
	@echo "Build & Release targets:"
	@echo "  build             Build all packages"
	@echo "  version           Show versions of all packages"
	@echo "  clean             Clean all packages"
	@echo ""
	@echo "Per-package targets (append package name):"
	@echo "  test-<package>    e.g., make test-chuk-virtual-expert"
	@echo "  build-<package>   e.g., make build-chuk-virtual-expert-time"
	@echo "  lint-<package>    e.g., make lint-chuk-virtual-expert-arithmetic"
	@echo ""
	@echo "Release targets (per-package only):"
	@echo "  publish-<package>       Create tag and push for GitHub Actions release"
	@echo "  publish-test-<package>  Upload package to TestPyPI"
	@echo "  bump-patch-<package>    Bump patch version for a package"
	@echo "  bump-minor-<package>    Bump minor version for a package"
	@echo "  bump-major-<package>    Bump major version for a package"

# ─── Workspace ────────────────────────────────────────────────────────────────

sync:
ifdef UV
	@echo "Syncing uv workspace..."
	uv sync --all-packages
else
	@echo "uv not found. Please install uv or use 'make dev-install' instead."
	@exit 1
endif

dev-install:
	@for pkg in $(PACKAGES); do \
		echo ""; \
		echo "══════ dev-install: $$(basename $$pkg) ══════"; \
		$(MAKE) -C $$pkg dev-install; \
	done

install:
	@for pkg in $(PACKAGES); do \
		echo ""; \
		echo "══════ install: $$(basename $$pkg) ══════"; \
		$(MAKE) -C $$pkg install; \
	done

# ─── Quality ──────────────────────────────────────────────────────────────────

test:
	@for pkg in $(PACKAGES); do \
		echo ""; \
		echo "══════ test: $$(basename $$pkg) ══════"; \
		$(MAKE) -C $$pkg test || exit 1; \
	done

test-cov:
	@for pkg in $(PACKAGES); do \
		echo ""; \
		echo "══════ test-cov: $$(basename $$pkg) ══════"; \
		$(MAKE) -C $$pkg test-cov || exit 1; \
	done

lint:
	@for pkg in $(PACKAGES); do \
		echo ""; \
		echo "══════ lint: $$(basename $$pkg) ══════"; \
		$(MAKE) -C $$pkg lint || exit 1; \
	done

format:
	@for pkg in $(PACKAGES); do \
		echo ""; \
		echo "══════ format: $$(basename $$pkg) ══════"; \
		$(MAKE) -C $$pkg format; \
	done

typecheck:
	@for pkg in $(PACKAGES); do \
		echo ""; \
		echo "══════ typecheck: $$(basename $$pkg) ══════"; \
		$(MAKE) -C $$pkg typecheck || exit 1; \
	done

security:
	@for pkg in $(PACKAGES); do \
		echo ""; \
		echo "══════ security: $$(basename $$pkg) ══════"; \
		$(MAKE) -C $$pkg security || exit 1; \
	done

check: lint typecheck security test
	@echo ""
	@echo "All checks passed for all packages!"

# ─── Build ────────────────────────────────────────────────────────────────────

build:
	@for pkg in $(PACKAGES); do \
		echo ""; \
		echo "══════ build: $$(basename $$pkg) ══════"; \
		$(MAKE) -C $$pkg build || exit 1; \
	done

version:
	@for pkg in $(PACKAGES); do \
		printf "%-40s " "$$(basename $$pkg):"; \
		grep '^version' $$pkg/pyproject.toml | sed 's/version = "\(.*\)"/\1/'; \
	done

clean:
	@for pkg in $(PACKAGES); do \
		echo ""; \
		echo "══════ clean: $$(basename $$pkg) ══════"; \
		$(MAKE) -C $$pkg clean; \
	done

# ─── Per-package targets ──────────────────────────────────────────────────────

# Generate per-package targets dynamically
define PACKAGE_TARGETS
test-$(1):
	@echo "══════ test: $(1) ══════"
	$(MAKE) -C packages/$(1) test

test-cov-$(1):
	@echo "══════ test-cov: $(1) ══════"
	$(MAKE) -C packages/$(1) test-cov

lint-$(1):
	@echo "══════ lint: $(1) ══════"
	$(MAKE) -C packages/$(1) lint

format-$(1):
	@echo "══════ format: $(1) ══════"
	$(MAKE) -C packages/$(1) format

typecheck-$(1):
	@echo "══════ typecheck: $(1) ══════"
	$(MAKE) -C packages/$(1) typecheck

security-$(1):
	@echo "══════ security: $(1) ══════"
	$(MAKE) -C packages/$(1) security

check-$(1):
	@echo "══════ check: $(1) ══════"
	$(MAKE) -C packages/$(1) check

build-$(1):
	@echo "══════ build: $(1) ══════"
	$(MAKE) -C packages/$(1) build

clean-$(1):
	@echo "══════ clean: $(1) ══════"
	$(MAKE) -C packages/$(1) clean

version-$(1):
	@printf "%-40s " "$(1):"
	@grep '^version' packages/$(1)/pyproject.toml | sed 's/version = "\(.*\)"/\1/'

publish-$(1):
	$(MAKE) -C packages/$(1) publish

publish-test-$(1):
	$(MAKE) -C packages/$(1) publish-test

publish-manual-$(1):
	$(MAKE) -C packages/$(1) publish-manual

bump-patch-$(1):
	$(MAKE) -C packages/$(1) bump-patch

bump-minor-$(1):
	$(MAKE) -C packages/$(1) bump-minor

bump-major-$(1):
	$(MAKE) -C packages/$(1) bump-major
endef

$(foreach pkg,$(PACKAGE_NAMES),$(eval $(call PACKAGE_TARGETS,$(pkg))))
