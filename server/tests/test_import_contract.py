import json
import sqlite3
from pathlib import Path


def test_be2_export_roundtrip_and_reference_integrity():
    root = Path(__file__).resolve().parents[1]/'data'
    manuals = json.loads((root/'manuals.json').read_text())
    rows = json.loads((root/'chunks.json').read_text())
    with sqlite3.connect(':memory:') as db:
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('CREATE TABLE manuals(id TEXT PRIMARY KEY,title TEXT,source TEXT,category TEXT)')
        db.execute('CREATE TABLE manual_chunks(id TEXT PRIMARY KEY,manual_id TEXT REFERENCES manuals(id),idx INTEGER,text TEXT)')
        db.executemany('INSERT INTO manuals VALUES(:id,:title,:source,:category)', manuals)
        db.executemany('INSERT INTO manual_chunks VALUES(:id,:manual_id,:idx,:text)', rows)
        assert db.execute('SELECT count(*) FROM manual_chunks').fetchone()[0] == len(rows)
        assert not db.execute('PRAGMA foreign_key_check').fetchall()
        assert all(r['text']==r['content'] and len(r['content']) <=500 for r in rows)
