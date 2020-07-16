# Contributing to aql

## Preparation

You'll need to have Python 3.6 or newer available for testing

You can do this with [pyenv][]:

    $ pyenv install 3.6.x
    $ pyenv shell 3.6.x


## Setup

Once in your development environment, install the
appropriate linting tools and dependencies:

    $ cd <path/to/aql>
    $ make venv
    $ source .venv/bin/activate


## Submitting

Before submitting a pull request, please ensure
that you have done the following:

* Documented changes or features in `README.md` and/or `docs/`
* Added appropriate license headers to new files
* Written or modified tests for new functionality
* Used `make format` to format code appropriately
* Validated code with `make lint test`

[pyenv]: https://github.com/pyenv/pyenv
