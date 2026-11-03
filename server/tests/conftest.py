"""Always isolate API tests from the developer's saved sessions."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from corpus_store import import_corpus


_database_dir = TemporaryDirectory(prefix="snapfix-tests-")
_previous_database = os.environ.get("SNAPFIX_DB")
_database = Path(_database_dir.name) / "test.db"
os.environ["SNAPFIX_DB"] = str(_database)
import_corpus(_database, Path(__file__).resolve().parents[1] / "data")


def pytest_sessionfinish(session, exitstatus):
    if _previous_database is None:
        os.environ.pop("SNAPFIX_DB", None)
    else:
        os.environ["SNAPFIX_DB"] = _previous_database
    _database_dir.cleanup()
