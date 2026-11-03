"""SQLite-backed sessions, feedback and report drafts."""
from collections.abc import MutableMapping
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import uuid


class SessionStore(MutableMapping):
    def __init__(self, path, decode):
        self.path = Path(path)
        self.decode = decode
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS sessions(
                    id TEXT PRIMARY KEY, device_category TEXT NOT NULL, brand TEXT, model TEXT,
                    error_code TEXT, decision TEXT NOT NULL, decision_reason TEXT NOT NULL,
                    safety_refused INTEGER NOT NULL, created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS steps(
                    id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                    idx INTEGER, content TEXT, citation_manual TEXT, citation_section TEXT, feedback TEXT);
                CREATE TABLE IF NOT EXISTS reports(
                    id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                    lang TEXT, content TEXT, created_at TEXT);
            ''')

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            yield db
        finally:
            db.close()

    def __getitem__(self, key):
        with self.connection() as db:
            row = db.execute('SELECT * FROM sessions WHERE id=?', (key,)).fetchone()
            if row is None:
                raise KeyError(key)
            data = dict(row)
            data['safety_refused'] = bool(data['safety_refused'])
            data['steps'] = [dict(step) for step in db.execute(
                'SELECT id,idx,content,citation_manual,citation_section,feedback '
                'FROM steps WHERE session_id=? ORDER BY idx', (key,))]
        return self.decode(data)

    def __setitem__(self, key, session):
        data = session.model_dump()
        if key != data['id']:
            raise ValueError('session ID mismatch')
        with self.connection() as db, db:
            db.execute('''INSERT INTO sessions VALUES(
                :id,:device_category,:brand,:model,:error_code,:decision,:decision_reason,:safety_refused,:created_at)
                ON CONFLICT(id) DO UPDATE SET device_category=excluded.device_category,
                brand=excluded.brand,model=excluded.model,error_code=excluded.error_code,
                decision=excluded.decision,decision_reason=excluded.decision_reason,
                safety_refused=excluded.safety_refused''', data)
            db.execute('DELETE FROM steps WHERE session_id=?', (key,))
            db.executemany('''INSERT INTO steps VALUES(
                :id,:session_id,:idx,:content,:citation_manual,:citation_section,:feedback)''',
                [{**step, 'session_id': key} for step in data['steps']])

    def __delitem__(self, key):
        with self.connection() as db, db:
            if not db.execute('DELETE FROM sessions WHERE id=?', (key,)).rowcount:
                raise KeyError(key)

    def __iter__(self):
        with self.connection() as db:
            ids = [row['id'] for row in db.execute('SELECT id FROM sessions')]
        return iter(ids)

    def __len__(self):
        with self.connection() as db:
            return db.execute('SELECT count(*) FROM sessions').fetchone()[0]

    def clear(self):
        with self.connection() as db, db:
            db.execute('DELETE FROM sessions')

    def save_report(self, session_id, lang, content):
        with self.connection() as db, db:
            db.execute('INSERT INTO reports VALUES(?,?,?,?,?)',
                       (str(uuid.uuid4()), session_id, lang, content, datetime.now(timezone.utc).isoformat()))

    def set_feedback(self, session_id, step_id, feedback):
        with self.connection() as db, db:
            return bool(db.execute('UPDATE steps SET feedback=? WHERE id=? AND session_id=?',
                                   (feedback, step_id, session_id)).rowcount)
