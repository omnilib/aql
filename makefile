PKG:=aql
EXTRAS:=dev,docs

.venv:
	python -m venv .venv
	source .venv/bin/activate && make install
	echo 'run `source .venv/bin/activate` to use virtualenv'

venv: .venv

install:
	python -m pip install -U pip
	python -m pip install -Ue .[$(EXTRAS)]

release: lint test clean
	flit publish

format:
	python -m usort format $(PKG)
	python -m black $(PKG)

lint:
	python -m flake8 $(PKG)
	python -m usort check $(PKG)
	python -m black --check $(PKG)

test:
	python -m coverage run -m $(PKG).tests
	python -m coverage report
	python -m mypy $(PKG)

html: .venv README.md docs/*.rst docs/conf.py
	source .venv/bin/activate && sphinx-build -b html docs html

clean:
	rm -rf build dist README MANIFEST *.egg-info .mypy_cache

distclean: clean
	rm -rf .venv
