[![Formatter](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PyPI version](https://badge.fury.io/py/alembic-migration-fixtures.svg)](https://pypi.org/project/alembic-migration-fixtures/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/alembic-migration-fixtures)](https://pypi.org/project/alembic-migration-fixtures/)


# Description
Pytest fixture to simplify writing tests against databases managed with `alembic`.
Before each test run, alembic migrations apply schema changes which then allows tests to only care about data.
This way your application code, and the database migrations get executed by the test.

Only tested with PosgreSQL. However, code may work with other databases as well.

# Installation

Install with `pip install alembic-migration-fixtures` or any other dependency manager.
Afterwards, create a pytest fixture called `database_engine` returning an SQLAlchemy `Engine` instance.

_WARNING_

Do not specify the production / development / any other database where data is important in the engine fixture.
If you do so, the tests WILL truncate all tables and data loss WILL occur.


# Usage

This library provides a pytest [fixture](https://docs.pytest.org/en/6.2.x/fixture.html) called `test_db_session`.
Use this to replace the normal SQLAlchemy session used within the application, or else tests may not be independent 
of one another. 

How the fixture works with your tests:
1. Fixture recreates (wipes) the database schema based on the engine provided for the test session
1. Fixture runs alembic migrations (equivalent to `alembic upgrade heads`)
1. Fixture creates a test database session within a transaction for the test
1. Your test sets up data and runs the test using the session (including `COMMIT`ing transactions)
1. Your test verifies data is in the database
1. Fixture rolls back the transaction (and any inner `COMMIT`ed transactions in the test)

This two-level transaction strategy makes it so any test is independent of one another, 
since the database is empty after each test. Since the database schema only gets re-created once per session,
the test speed is only linearly dependent on the number of migrations.


# Development

This library uses the [poetry](https://python-poetry.org/) package manager, which has to be installed before installing
other dependencies. Afterwards, run `poetry install` to create a virtualenv and install all dependencies.
To then activate that environment, use `poetry shell`. To run a command in the environment without activating it,
use `poetry run <command>`.

[Black](https://github.com/psf/black) is used (and enforced via workflows) to format all code. Poetry will install it
automatically, but running it is up to the user. To format the entire project, run `black .` inside the virtualenv.

# Contributing

This project uses the Apache 2.0 license and is maintained by the data science team @ Barbora. All contribution are 
welcome in the form of PRs or raised issues.
