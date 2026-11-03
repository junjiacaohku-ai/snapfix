from main import Session, _mock_router
from session_store import SessionStore


def test_feedback_and_reports_survive_reopen_and_delete_cascades(tmp_path):
    path = tmp_path / 'sessions.db'
    first = SessionStore(path, Session.model_validate)
    session = _mock_router()
    session.steps[0].feedback = 'done'
    first[session.id] = session
    first.save_report(session.id, 'en', 'Please help with the router.')

    reopened = SessionStore(path, Session.model_validate)
    assert reopened[session.id].steps[0].feedback == 'done'
    assert reopened.set_feedback(session.id, session.steps[1].id, 'skipped')
    assert first.set_feedback(session.id, session.steps[0].id, 'not_useful')
    assert reopened[session.id].steps[1].feedback == 'skipped'
    with reopened.connection() as db:
        assert db.execute('SELECT content FROM reports').fetchone()[0] == 'Please help with the router.'
    del reopened[session.id]
    with reopened.connection() as db:
        for table in ['sessions', 'steps', 'reports']:
            assert db.execute(f'SELECT count(*) FROM {table}').fetchone()[0] == 0
        assert not db.execute('PRAGMA foreign_key_check').fetchall()
