build:
	python3 setup.py build

dev:
	python3 setup.py develop

setup:
	python3 -m pip install -Ur requirements-dev.txt

venv:
	python3 -m venv .venv
	source .venv/bin/activate && make setup dev
	echo 'run `source .venv/bin/activate` to use virtualenv'

release: lint test clean
	python3 setup.py sdist
	python3 -m twine upload dist/*

black:
	python3 -m isort --apply --recursive aql setup.py
	python3 -m black aql setup.py

lint:
	python3 -m mypy aql
	python3 -m pylint --rcfile .pylint aql setup.py
	python3 -m isort --diff --recursive aql setup.py
	python3 -m black --check aql setup.py

test:
	python3 -m coverage run -m aql.tests
	python3 -m coverage report
	python3 -m coverage html

clean:
	rm -rf build dist README MANIFEST *.egg-info
