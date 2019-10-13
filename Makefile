build:
	python3 setup.py sdist bdist_wheel

upload-test:
	python3 -m twine upload --skip-existing --repository-url https://test.pypi.org/legacy/ dist/*

upload:
	python3 -m twine upload --skip-existing dist/*

publish-test: build upload-test

publish: build upload

test-cov:
	pytest --cov=argser --no-cov-on-fail --cov-report html --cov-report term-missing
