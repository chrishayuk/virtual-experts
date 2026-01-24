.PHONY: install test test-cov lint format typecheck security check demo clean

install:
	uv pip install -e ".[dev]"

test:
	python3 -m pytest tests/ -v

test-cov:
	python3 -m pytest tests/ --cov=chuk_virtual_expert_mcts --cov-report=term-missing --cov-fail-under=90

lint:
	@echo "Running ruff checks..."
	ruff check src/ tests/
	@echo "Checking formatting..."
	ruff format --check src/ tests/

format:
	@echo "Formatting code with ruff..."
	ruff format src/ tests/
	@echo "Fixing linting issues..."
	ruff check --fix src/ tests/

typecheck:
	@echo "Running mypy type checking..."
	mypy src/

security:
	@echo "Running bandit security checks..."
	bandit -r src/ -ll

check: lint typecheck security test
	@echo "All checks passed!"

demo:
	python3 examples/demo.py

clean:
	rm -rf build/ dist/ *.egg-info src/*.egg-info .pytest_cache .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
