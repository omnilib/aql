build:
	python setup.py build

dev:
	python setup.py develop

setup:
	python -m pip install -Ur requirements-dev.txt

venv:
	python -m venv .venv
	source .venv/bin/activate && make setup dev
	echo 'run `source .venv/bin/activate` to use virtualenv'

release: lint test clean
	python setup.py sdist
	python -m twine upload dist/*

black:
	python -m isort --apply --recursive aql setup.py
	python -m black aql setup.py

lint:
	python -m mypy aql
	python -m pylint --rcfile .pylint aql setup.py
	python -m isort --diff --recursive aql setup.py
	python -m black --check aql setup.py

test:
	python -m coverage run -m aql.tests
	python -m coverage report
	python -m coverage html

clean:
	rm -rf build dist README MANIFEST *.egg-info
