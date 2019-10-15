publish:
	poetry build && poetry publish

test:
	pytest --cov=argser --no-cov-on-fail --cov-report html --cov-report term-missing
