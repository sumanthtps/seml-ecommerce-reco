.DEFAULT_GOAL := help
PYTHON ?= python
COMPOSE ?= docker compose

.PHONY: help install seed train command query demo verify lint format typecheck \
        test cov check notebook word report docker-build up down logs clean

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-14s %s\n", $$1, $$2}'

install: ## Install runtime, development, and report dependencies
	$(PYTHON) -m pip install -r requirements.txt -e ".[dev,report]"

seed: ## Generate deterministic demonstration interactions
	$(PYTHON) scripts/seed_data.py

train: ## Train, evaluate, and persist the recommendation model
	$(PYTHON) scripts/train_and_evaluate.py

command: ## Run the CQRS command service on port 8101
	uvicorn ecom_ml.command_service.main:app --reload --port 8101

query: ## Run the CQRS query service on port 8102
	uvicorn ecom_ml.query_service.main:app --reload --port 8102

demo: ## Exercise two already-running services
	$(PYTHON) scripts/run_demo.py

verify: ## Start both services temporarily and run an end-to-end check
	$(PYTHON) scripts/verify_live.py

lint: ## Lint source, tests, scripts, and generators
	ruff check src tests scripts tools

format: ## Format and auto-fix Python files
	ruff format src tests scripts tools
	ruff check --fix src tests scripts tools

typecheck: ## Run static type checks
	mypy --cache-dir=/tmp/seml-mypy-cache

test: ## Run automated tests
	pytest

cov: ## Run tests with branch coverage
	pytest --cov=ecom_ml --cov-report=term-missing

check: lint typecheck cov ## Run the local CI quality gate
	ruff format --check src tests scripts tools

notebook: ## Rebuild and execute the submission notebook
	$(PYTHON) tools/build_notebook.py

word: ## Regenerate diagrams and the Word report
	$(PYTHON) tools/generate_assets.py
	$(PYTHON) tools/build_report.py

report: ## Regenerate diagrams, notebook, Word report, and optional PDF
	$(PYTHON) tools/generate_assets.py
	$(PYTHON) tools/build_notebook.py
	$(PYTHON) tools/build_report.py --with-pdf

docker-build: ## Build the runtime container
	$(COMPOSE) build

up: ## Start both services with Docker Compose
	$(COMPOSE) up --build

down: ## Stop the Compose stack
	$(COMPOSE) down

logs: ## Follow service logs
	$(COMPOSE) logs -f

clean: ## Remove local caches and generated temporary output
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage coverage.xml htmlcov tmp output
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
