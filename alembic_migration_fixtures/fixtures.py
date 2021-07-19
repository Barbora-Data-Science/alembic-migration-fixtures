"""Pytest fixtures to keep the test database clean each time tests are run."""
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import alembic.config
import sqlalchemy
from _pytest.config.argparsing import Parser
from _pytest.fixtures import FixtureRequest, fixture
from alembic import command
from sqlalchemy.orm import Session


def pytest_addoption(parser: Parser) -> None:
    """Add CLI overrides for where to run alembic commands.

    Args:
        parser: pytest's command line argument parser to add options to.
    """
    parser.addoption(
        "--alembic-folder",
        default=Path("./migrations"),
        type=Path,
        help="folder (from the test root) where alembic commands should be run from",
    )


@fixture(scope="session")
def _with_test_db(database_engine: sqlalchemy.engine.Engine, request: FixtureRequest) -> None:
    """Fixture for database setup before running tests.

    Args:
        database_engine: SQLAlchemy engine to use for cleaning up the database.
        request: Pytest request to get configuration from.
    """
    with _real_db_session(database_engine) as session:
        _wipe_db_schema(session)
    alembic_folder = Path(request.config.rootdir) / request.config.getoption("--alembic-folder")
    _run_db_schema_migrations(str(database_engine.url), str(alembic_folder))


@fixture(scope="function")
def test_db_session(database_engine: sqlalchemy.engine.Engine, _with_test_db) -> Iterator[Session]:
    """Create a database session that will rollback even if commits are issued during the test.

    Args:
        database_engine: SQLAlchemy engine to use to connect to the database.

    Returns:
        Test-ready automatically rolled back database session. Should be used to override any
            production sessions used in the application.
    """
    # get a new database transaction to wrap any transactions used in the test or tested code
    connection = database_engine.connect()
    transaction = connection.begin()
    # bind the database session to this outer transaction
    session = Session(bind=connection)
    yield session
    # rollback everything the test committed and clean up
    transaction.rollback()
    connection.close()
    session.close()


def _wipe_db_schema(session: Session, schema: str = "public") -> None:
    """Wipes everything in a database's schema.

    Args:
        session: SQLAlchemy database session to use.
        schema: Name of the database schema which needs to be wiped.
    """
    session.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE;")
    session.commit()
    session.execute(f"CREATE SCHEMA {schema};")
    session.commit()


def _run_db_schema_migrations(sqlalchemy_url: str, script_location: str) -> None:
    """Runs Alembic migrations to build the database schema.

    Args:
        sqlalchemy_url: Connection string of the database to migrate.
        script_location: Path to the folder where alembic scripts can be run.
    """
    config = alembic.config.Config()
    config.set_main_option("script_location", script_location)
    config.set_main_option("sqlalchemy.url", sqlalchemy_url)
    # heads means all migrations from all branches (in case there are split branches)
    command.upgrade(config, "heads")


@contextmanager
def _real_db_session(engine: sqlalchemy.engine.Engine) -> Iterator[Session]:
    """Context manager for a normal SQLAlchemy session to be used during before test setup.

    Args:
        engine: SQLAlchemy engine to use to connect to the database.

    Returns:
        Self-closing SQLAlchemy session.
    """
    connection = engine.connect()
    session = Session(bind=connection)
    yield session
    connection.close()
    session.close()
