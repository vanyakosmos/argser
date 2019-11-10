.PHONY: test docs

clean:
	@rm -rf build dist .eggs *.egg-info
	@rm -rf .benchmarks .coverage coverage.xml htmlcov report.xml .tox
	@find . -type d -name '.mypy_cache' -exec rm -rf {} +
	@find . -type d -name '__pycache__' -exec rm -rf {} +
	@find . -type d -name '*pytest_cache*' -exec rm -rf {} +
	@find . -type f -name "*.py[co]" -exec rm -rf {} +

format: clean
	@black argser/ tests/

test:
	@pytest --cov=argser --no-cov-on-fail --cov-report html --cov-report term-missing -q

docs:
	@make -C docs clean
	@make -C docs html
