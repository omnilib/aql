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

format:
	python -m usort format aql
	python -m black aql

lint:
	python -m mypy aql
	python -m pylint --rcfile .pylint aql
	python -m usort check aql
	python -m black --check aql

test:
	python -m coverage run -m aql.tests
	python -m coverage report
	python -m coverage html

html: .venv README.md docs/*.rst docs/conf.py
	source .venv/bin/activate && sphinx-build -b html docs html

clean:
	rm -rf build dist README MANIFEST *.egg-info .mypy_cache

distclean: clean
	rm -rf .venv