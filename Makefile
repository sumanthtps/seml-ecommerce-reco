.DEFAULT_GOAL := help
PYTHON ?= python
COMPOSE ?= docker compose

.PHONY: help install install-dev lint format typecheck test cov check \
        run-reco run-gateway demo evidence docker-build up down logs clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: ## Install runtime package
	$(PYTHON) -m pip install -e .

install-dev: ## Install package with dev + evidence extras and pre-commit hooks
	$(PYTHON) -m pip install -e ".[dev,evidence]"
	pre-commit install

lint: ## Lint with ruff
	ruff check src tests scripts

format: ## Auto-format and auto-fix with ruff
	ruff format src tests scripts
	ruff check --fix src tests scripts

typecheck: ## Static type check with mypy
	mypy

test: ## Run the test suite
	pytest

cov: ## Run tests with coverage report
	pytest --cov=reco --cov-report=term-missing

check: lint typecheck test ## Run lint + types + tests (what CI runs)

run-reco: ## Run the recommendation service locally (port 8001)
	uvicorn reco.recommendation.main:app --reload --port 8001

run-gateway: ## Run the API gateway locally (port 8000)
	uvicorn reco.gateway.main:app --reload --port 8000

demo: ## Send a demo scenario through the running gateway
	$(PYTHON) scripts/run_demo.py

evidence: ## Generate offline metrics + plot into artifacts/
	$(PYTHON) scripts/generate_evidence.py

docker-build: ## Build the container image
	$(COMPOSE) build

up: ## Start both services with docker compose
	$(COMPOSE) up --build

down: ## Stop and remove the compose stack
	$(COMPOSE) down

logs: ## Tail compose logs
	$(COMPOSE) logs -f

clean: ## Remove caches and build artifacts
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage build dist *.egg-info artifacts
