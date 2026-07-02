# Throughline — developer commands (source of truth; mirrored in CLAUDE.md)
.DEFAULT_GOAL := help
SHELL := /bin/bash
VENV := .venv
PY := $(VENV)/bin/python
PYTEST := $(VENV)/bin/pytest

.PHONY: help setup setup-py setup-web dev dev-api dev-web test test-py test-web \
        e2e lint lint-py lint-web typecheck typecheck-py typecheck-web evals \
        check-rates fmt clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

setup: setup-py setup-web ## Install all deps (python + web)

setup-py: ## Create venv and install python deps (editable + dev)
	uv venv $(VENV) --python 3.11
	uv pip install --python $(VENV) -e ".[dev]"

setup-web: ## Install web deps
	cd apps/web && pnpm install --frozen-lockfile || (cd apps/web && pnpm install)

dev: ## Run api + web together
	@$(MAKE) -j2 dev-api dev-web

dev-api: ## Run the FastAPI dev server
	$(VENV)/bin/uvicorn throughline_api.app:app --reload --app-dir services/api --port 8000

dev-web: ## Run the Next.js dev server
	cd apps/web && pnpm dev

test: test-py ## Run all unit tests (python). test-web when web has tests.

test-py: ## Run python unit tests
	$(PYTEST)

test-web: ## Run web unit tests
	cd apps/web && pnpm test --run || echo "(no web tests yet)"

e2e: ## Run end-to-end tests
	cd apps/web && pnpm e2e || echo "(no e2e yet)"

lint: lint-py ## Lint everything
lint-py: ## Ruff lint + format check
	$(VENV)/bin/ruff check services ml evals
	$(VENV)/bin/ruff format --check services ml evals

lint-web: ## ESLint + prettier
	cd apps/web && pnpm lint

typecheck: typecheck-py ## Typecheck everything
typecheck-py: ## pyright
	$(VENV)/bin/pyright

typecheck-web: ## tsc --noEmit
	cd apps/web && pnpm typecheck

evals: ## Run eval-gated suites (BEFORE merging any AI-feature change)
	$(PYTEST) -m eval evals

check-rates: ## Fail if a rate/hour-threshold literal is hard-coded in rules/budget code
	$(PY) scripts/check_no_hardcoded_rates.py

fmt: ## Auto-format python
	$(VENV)/bin/ruff format services ml evals
	$(VENV)/bin/ruff check --fix services ml evals

clean: ## Remove caches + venv
	rm -rf $(VENV) .pytest_cache **/__pycache__ **/.ruff_cache
