PYTHON		= python3
PIP			= pip
MAIN		= main.py
MAP			?= maps/hard/02_capacity_hell.txt


install:
	uv add -r requirements.txt
	uv sync

run:
	uv run $(PYTHON) $(MAIN) $(MAP)

debug:
	$(PYTHON) -m pdb $(MAIN) $(MAP)

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports \
		--disallow-untyped-defs --check-untyped-defs


lint-strict:
	flake8 .
	mypy . --strict


re: clean run

.PHONY: install run debug clean lint lint-strict re
