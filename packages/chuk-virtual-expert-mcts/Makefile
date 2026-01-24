.PHONY: install test coverage lint clean demo

install:
	uv pip install -e ".[dev]"

test:
	python -m pytest tests/ -v

coverage:
	python -m pytest tests/ --cov=chuk_virtual_expert_mcts --cov-report=term-missing --cov-fail-under=90

lint:
	python -m ruff check src/ tests/

demo:
	python examples/demo.py

clean:
	rm -rf build/ dist/ *.egg-info src/*.egg-info .pytest_cache .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
