build:
	python3 setup.py build

dev:
	python3 setup.py develop

setup:
	pip3 install -U black isort mypy pylint twine

venv:
	python3 -m virtualenv .venv
	source .venv/bin/activate && make setup dev
	echo 'run `source .venv/bin/activate` to use virtualenv'

release: lint test clean
	python3 setup.py sdist
	python3 -m twine upload dist/*

black:
	isort --apply --multi-line=3 --trailing-comma --force-grid-wrap=0 \
		--use-parentheses --line-width=88 --recursive aql setup.py
	black aql setup.py

lint:
	isort --diff --multi-line=3 --trailing-comma --force-grid-wrap=0 \
		--use-parentheses --line-width=88 --recursive aql setup.py
	black --check aql setup.py
	pylint --rcfile .pylint aql setup.py
	mypy --ignore-missing-imports aql

test:
	python3 -m unittest -v aql.tests

clean:
	rm -rf build dist README MANIFEST .venv *.egg-info
