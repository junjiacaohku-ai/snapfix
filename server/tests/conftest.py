"""Always isolate API tests from the developer's saved sessions."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory


_database_dir = TemporaryDirectory(prefix='snapfix-tests-')
_previous_database = os.environ.get('SNAPFIX_DB')
os.environ['SNAPFIX_DB'] = str(Path(_database_dir.name) / 'test.db')


def pytest_sessionfinish(session, exitstatus):
    if _previous_database is None:
        os.environ.pop('SNAPFIX_DB', None)
    else:
        os.environ['SNAPFIX_DB'] = _previous_database
    _database_dir.cleanup()
