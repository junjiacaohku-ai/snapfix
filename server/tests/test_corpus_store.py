import json
from pathlib import Path
import sqlite3
import pytest
from corpus_store import import_corpus, read_chunks
from retrieval import Retriever


DATA = Path(__file__).resolve().parents[1] / 'data'


def test_import_survives_reopen_is_idempotent_and_preserves_other_manuals(tmp_path):
    db_path = tmp_path / 'corpus.sqlite'
    expected = import_corpus(db_path, DATA)
    with sqlite3.connect(db_path) as db:
        db.execute("INSERT INTO manuals(id,title) VALUES('unrelated','Keep me')")
        db.execute("INSERT INTO manual_chunks VALUES('unrelated-chunk','unrelated',0,'Other work')")
    assert import_corpus(db_path, DATA) == expected
    rows = read_chunks(db_path)
    assert len(rows) == expected['chunks']
    with sqlite3.connect(db_path) as db:
        assert db.execute("SELECT text FROM manual_chunks WHERE id='unrelated-chunk'").fetchone() == ('Other work',)
        assert not db.execute('PRAGMA foreign_key_check').fetchall()
    results = Retriever(rows).search('博世 E:24 排水', brand='Bosch', category='dishwasher', error_code='E24')
    assert results and results[0]['manual_id'] == 'bosch-dishwasher-9001014024'
    assert results[0]['page'] == 35


def test_invalid_import_keeps_existing_data(tmp_path):
    db_path = tmp_path / 'corpus.sqlite'
    import_corpus(db_path, DATA)
    before = read_chunks(db_path)
    bad = tmp_path / 'bad'
    bad.mkdir()
    (bad / 'manuals.json').write_text((DATA / 'manuals.json').read_text())
    rows = json.loads((DATA / 'chunks.json').read_text())
    rows[0]['manual_id'] = 'missing'
    (bad / 'chunks.json').write_text(json.dumps(rows))
    with pytest.raises(ValueError):
        import_corpus(db_path, bad)
    assert read_chunks(db_path) == before
