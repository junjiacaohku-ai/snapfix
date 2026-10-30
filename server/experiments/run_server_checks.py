"""Real HTTP/restart checks against an isolated database; no API keys needed."""
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from corpus_store import import_corpus, read_chunks
from retrieval import Retriever


def run():
    with tempfile.TemporaryDirectory(prefix='snapfix-http-') as directory:
        database = Path(directory) / 'snapfix.db'
        imported = import_corpus(database, ROOT/'data')
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        origin = f'http://127.0.0.1:{port}'
        environment = {**os.environ, 'SNAPFIX_DB': str(database)}

        def request(path, payload=None, method=None):
            body = json.dumps(payload).encode() if payload is not None else None
            req = urllib.request.Request(origin+path, data=body, method=method,
                                         headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req, timeout=5) as response:
                return json.load(response)

        def start():
            process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'main:app',
                                        '--host', '127.0.0.1', '--port', str(port)],
                                       cwd=ROOT, env=environment, stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL)
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError('server exited before startup')
                try:
                    request('/api/health')
                    return process
                except OSError:
                    time.sleep(.05)
            stop(process)
            raise RuntimeError('server startup timeout')

        def stop(process):
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

        process = start()
        try:
            session = request('/api/diagnose/manual', {'brand':'Bosch','error_code':'E:24'})
            path = '/api/sessions/'+session['id']
            request(path+'/steps/'+session['steps'][0]['id']+'/feedback', {'feedback':'done'})
            report = request(path+'/report', {'lang':'en'})
            assert 'step 1' in report['content']
            with urllib.request.urlopen(origin+'/docs', timeout=5) as response:
                docs_status = response.status
        finally:
            stop(process)
        process = start()
        try:
            restored = request(path)
            assert restored['steps'][0]['feedback']=='done'
            with sqlite3.connect(database) as db:
                assert db.execute('SELECT count(*) FROM reports WHERE session_id=?',
                                  (session['id'],)).fetchone()[0] == 1
            request(path, method='DELETE')
            with sqlite3.connect(database) as db:
                assert db.execute('SELECT count(*) FROM steps').fetchone()[0] == 0
                assert db.execute('SELECT count(*) FROM reports').fetchone()[0] == 0
            hits = Retriever(read_chunks(database)).search('E24 drain', brand='Bosch',
                                                          category='dishwasher', error_code='E24')
            assert hits and hits[0]['page']==35
        finally:
            stop(process)
        results = dict(health={'status':'ok','mock':True,'provider':'mock'},
                       docs_http_status=docs_status, imported=imported,
                       restart_preserves_feedback=True, restart_preserves_report=True,
                       deletion_cascades=True, sqlite_retrieval_page=hits[0]['page'],
                       scope='Real Uvicorn HTTP and SQLite restart; diagnosis still offline; no phone UI test')
        (ROOT/'experiments/server-check.json').write_text(json.dumps(results,indent=2)+'\n')
        print(json.dumps(results))


if __name__ == '__main__':
    run()
