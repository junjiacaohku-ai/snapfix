import os
from pathlib import Path
from tempfile import TemporaryDirectory

# Runs before test modules import main: no developer database is opened.
_database_dir = TemporaryDirectory(prefix="snapfix-week2-tests-")
_previous = os.environ.get("SNAPFIX_DB")
os.environ["SNAPFIX_DB"] = str(Path(_database_dir.name) / "startup.db")


def pytest_sessionfinish(session, exitstatus):
    if _previous is None:
        os.environ.pop("SNAPFIX_DB", None)
    else:
        os.environ["SNAPFIX_DB"] = _previous
    _database_dir.cleanup()