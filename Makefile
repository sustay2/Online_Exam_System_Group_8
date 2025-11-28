.PHONY: format lint test ci

format:
	@echo "Formatting..."
	black .
	isort .

lint:
	@echo "Linting & type checking..."
	ruff check .
	black --check .
	mypy src

test:
	@echo "Running tests..."
	pytest -q

ci: lint test
	@echo "CI pipeline completed successfully!"
