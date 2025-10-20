.PHONY: help install test run lint clean format type-check coverage dev-setup

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Neura - Local-first Cognitive Operating System$(NC)"
	@echo "$(YELLOW)Available commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'

install: ## Install dependencies with Poetry
	@echo "$(BLUE)Installing dependencies...$(NC)"
	poetry install --no-root
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

dev-setup: install ## Setup development environment
	@echo "$(BLUE)Setting up development environment...$(NC)"
	poetry run pre-commit install
	mkdir -p data logs
	@echo "$(GREEN)✓ Development environment ready$(NC)"

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	poetry run pytest

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	poetry run pytest tests/unit/

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	poetry run pytest tests/integration/

test-security: ## Run security tests only
	@echo "$(BLUE)Running security tests...$(NC)"
	poetry run pytest tests/security/

coverage: ## Generate coverage report
	@echo "$(BLUE)Generating coverage report...$(NC)"
	poetry run pytest --cov-report=html --cov-report=term
	@echo "$(GREEN)✓ Coverage report: htmlcov/index.html$(NC)"

run: ## Run Neura API server
	@echo "$(BLUE)Starting NeuraCore API...$(NC)"
	poetry run uvicorn neura.core.api:app --reload --host 0.0.0.0 --port 8000

run-prod: ## Run in production mode
	@echo "$(BLUE)Starting NeuraCore API (production)...$(NC)"
	poetry run uvicorn neura.core.api:app --host 0.0.0.0 --port 8000 --workers 4

format: ## Format code with Black
	@echo "$(BLUE)Formatting code...$(NC)"
	poetry run black neura/ tests/
	@echo "$(GREEN)✓ Code formatted$(NC)"

lint: ## Lint code with Ruff
	@echo "$(BLUE)Linting code...$(NC)"
	poetry run ruff check neura/ tests/
	@echo "$(GREEN)✓ Code linted$(NC)"

type-check: ## Type check with mypy
	@echo "$(BLUE)Type checking...$(NC)"
	poetry run mypy neura/
	@echo "$(GREEN)✓ Type checking complete$(NC)"

check: format lint type-check test ## Run all checks (format, lint, type-check, test)
	@echo "$(GREEN)✓ All checks passed$(NC)"

clean: ## Clean generated files and caches
	@echo "$(BLUE)Cleaning...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage dist/ build/
	@echo "$(GREEN)✓ Cleaned$(NC)"

docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	poetry run mkdocs build
	@echo "$(GREEN)✓ Documentation: site/index.html$(NC)"

docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation at http://127.0.0.1:8001$(NC)"
	poetry run mkdocs serve -a 127.0.0.1:8001

shell: ## Open Poetry shell
	poetry shell
