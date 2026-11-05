"""Import the D-line export into SQLite without replacing unrelated manuals."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3


def import_corpus(database, data_dir):
    data_dir = Path(data_dir)
    manuals = json.loads((data_dir / 'manuals.json').read_text())
    chunks = json.loads((data_dir / 'chunks.json').read_text())
    manual_ids = {m['id'] for m in manuals}
    if len(manual_ids) != len(manuals) or len({c['id'] for c in chunks}) != len(chunks):
        raise ValueError('duplicate manual or chunk ID')
    positions = set()
    for chunk in chunks:
        position = (chunk['manual_id'], chunk['idx'])
        if (chunk['manual_id'] not in manual_ids or position in positions
                or not chunk['text'].strip() or len(chunk['text']) > 500
                or chunk['text'] != chunk['content']):
            raise ValueError(f'invalid chunk: {chunk["id"]}')
        positions.add(position)
    Path(database).parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(database)) as db:
        db.execute('PRAGMA foreign_keys=ON')
        db.executescript('''
            CREATE TABLE IF NOT EXISTS manuals (
                id TEXT PRIMARY KEY, title TEXT, source TEXT, category TEXT, created_at TEXT);
            CREATE TABLE IF NOT EXISTS manual_chunks (
                id TEXT PRIMARY KEY, manual_id TEXT REFERENCES manuals(id), idx INTEGER, text TEXT);
            CREATE TABLE IF NOT EXISTS chunk_metadata (
                chunk_id TEXT PRIMARY KEY REFERENCES manual_chunks(id) ON DELETE CASCADE,
                metadata_json TEXT NOT NULL);
        ''')
        with db:
            for manual in manuals:
                db.execute('''INSERT INTO manuals(id,title,source,category,created_at)
                    VALUES(:id,:title,:source,:category,:created_at)
                    ON CONFLICT(id) DO UPDATE SET title=excluded.title,
                    source=excluded.source, category=excluded.category''',
                    {**manual, 'created_at': datetime.now(timezone.utc).isoformat()})
                db.execute('DELETE FROM chunk_metadata WHERE chunk_id IN '
                           '(SELECT id FROM manual_chunks WHERE manual_id=?)', (manual['id'],))
                db.execute('DELETE FROM manual_chunks WHERE manual_id=?', (manual['id'],))
            db.executemany('INSERT INTO manual_chunks(id,manual_id,idx,text) VALUES(:id,:manual_id,:idx,:text)', chunks)
            db.executemany('INSERT INTO chunk_metadata VALUES(?,?)',
                           [(c['id'], json.dumps(c, ensure_ascii=False)) for c in chunks])
    return {'manuals': len(manuals), 'chunks': len(chunks)}


def read_chunks(database):
    # Read-only reopen verifies that callers don't depend on an in-memory connection.
    uri = Path(database).resolve().as_uri() + '?mode=ro'
    with closing(sqlite3.connect(uri, uri=True)) as db:
        return [{**json.loads(meta), 'id': id_, 'manual_id': manual_id, 'idx': idx,
                 'text': text, 'content': text}
                for id_, manual_id, idx, text, meta in db.execute('''
                    SELECT c.id,c.manual_id,c.idx,c.text,m.metadata_json
                    FROM manual_chunks c JOIN chunk_metadata m ON m.chunk_id=c.id
                    ORDER BY c.manual_id,c.idx''')]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--data', type=Path, default=Path(__file__).parent / 'data')
    args = parser.parse_args()
    print(json.dumps(import_corpus(args.database, args.data)))
