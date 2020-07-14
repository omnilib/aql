.venv:
	python -m venv .venv
	source .venv/bin/activate && make setup dev
	echo 'run `source .venv/bin/activate` to use virtualenv'

venv: .venv

dev:
	flit install --symlink

setup:
	python -m pip install -Ur requirements-dev.txt

release: lint test clean
	flit publish

black:
	python -m isort --apply --recursive aql
	python -m black aql

lint:
	python -m mypy aql
	python -m pylint --rcfile .pylint aql
	python -m isort --diff --recursive aql
	python -m black --check aql

test:
	python -m coverage run -m aql.tests
	python -m coverage report
	python -m coverage html

clean:
	rm -rf build dist README MANIFEST *.egg-info .mypy_cache

distclean: clean
	rm -rf .venv