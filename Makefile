.PHONY: help install install-dev lint format typecheck test test-cov preflight dry-run clean

# ── Help ───────────────────────────────────────────────────────────────────────
help:
	@echo "LD Course Factory — dev commands"
	@echo ""
	@echo "  make install       Install runtime dependencies"
	@echo "  make install-dev   Install all dependencies including dev tools"
	@echo "  make lint          Run ruff linter"
	@echo "  make format        Run black formatter"
	@echo "  make typecheck     Run mypy type checker"
	@echo "  make test          Run test suite"
	@echo "  make test-cov      Run tests with coverage report"
	@echo "  make preflight     Run preflight checks"
	@echo "  make dry-run       Run pipeline with dry_run provider"
	@echo "  make clean         Remove generated artifacts"

# ── Dependencies ──────────────────────────────────────────────────────────────
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt
	pre-commit install

# ── Code quality ──────────────────────────────────────────────────────────────
lint:
	ruff check orchestrator/ ui/ cli/ services/ utils/ governance/ schemas/ adk/

format:
	black orchestrator/ ui/ cli/ services/ utils/ governance/ schemas/ adk/ scripts/

typecheck:
	mypy orchestrator/ utils/ governance/ services/

# ── Tests ─────────────────────────────────────────────────────────────────────
test:
	pytest tests/ -x

test-cov:
	pytest tests/ --cov --cov-report=term-missing --cov-report=html:htmlcov

# ── Pipeline shortcuts ────────────────────────────────────────────────────────
preflight:
	python3 scripts/preflight_check.py

dry-run:
	PROVIDER=dry_run AUTO_APPROVE=1 python3 scripts/run_pipeline.py \
	    --skip_preflight --yes --auto_approve

ui:
	streamlit run app.py

# ── Cleanup ───────────────────────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .mypy_cache .ruff_cache htmlcov .pytest_cache
