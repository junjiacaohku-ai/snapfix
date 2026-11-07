"""Check the public-photo substitution pack against offline APIs, without live vision."""
import hashlib
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import time

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
MANIFEST = REPO / 'docs/demo-assets/alternatives/manifest.json'


def evaluate():
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    assets = {item['id']: item for item in manifest['assets']}
    for asset in assets.values():
        path = (REPO / asset['source_file']).resolve()
        if not path.is_relative_to(REPO.resolve()):
            raise ValueError('Image must remain inside repository')
        if hashlib.sha256(path.read_bytes()).hexdigest() != asset['sha256']:
            raise ValueError(f'Changed input: {asset["id"]}')
    with TemporaryDirectory(prefix='snapfix-alternatives-') as folder:
        os.environ['SNAPFIX_DB'] = str(Path(folder) / 'checks.db')
        sys.path.insert(0, str(ROOT))
        from corpus_store import import_corpus
        from fastapi.testclient import TestClient
        from main import app

        import_corpus(os.environ['SNAPFIX_DB'], ROOT / 'data')

        results = []
        with TestClient(app) as client:
            assert client.get('/api/health').json()['mock'] is True
            for case in manifest['cases']:
                start = time.perf_counter()
                if case['kind'] == 'manual':
                    response = client.post('/api/diagnose/manual', json=case['payload'])
                else:
                    asset = assets[case['asset']]
                    mime = 'image/png' if asset['demo_name'].endswith('.png') else 'image/jpeg'
                    response = client.post('/api/analyze/image', files={
                        'file': (asset['demo_name'], (REPO / asset['source_file']).read_bytes(), mime)})
                data = response.json()
                checks = {'http_status': response.status_code == case['expected']['status']}
                for key, expected in case['expected'].items():
                    if key == 'retake':
                        checks[key] = '重拍' in data.get('detail', '')
                    elif key != 'status':
                        checks[key] = key in data and data[key] == expected
                reports = {}
                if case.get('exercise_report'):
                    checks.update(feedback_saved=False, reports=False, archive_read=False)
                    if response.status_code == 200 and data.get('steps'):
                        url = f'/api/sessions/{data["id"]}'
                        feedback = client.post(f'{url}/steps/{data["steps"][0]["id"]}/feedback',
                                               json={'feedback': 'done'})
                        saved = client.get(url)
                        checks['feedback_saved'] = (feedback.status_code == 200 and saved.status_code == 200
                                                    and saved.json()['steps'][0]['feedback'] == 'done')
                        responses = {lang: client.post(url + '/report', json={'lang': lang})
                                     for lang in ['zh', 'en']}
                        reports = {lang: item.json() for lang, item in responses.items()}
                        checks['reports'] = (all(item.status_code == 200 for item in responses.values())
                            and '步骤1' in reports['zh'].get('content', '')
                            and 'step 1' in reports['en'].get('content', '').lower()
                            and 'attach a photo' in reports['en'].get('content', ''))
                        archive = client.get('/api/sessions')
                        checks['archive_read'] = (archive.status_code == 200
                            and any(item['id'] == data['id'] for item in archive.json()))
                results.append(dict(case=case['id'], scenario=case['scenario'], status=response.status_code,
                    checks=checks, passed=all(checks.values()), response=data, reports=reports,
                    elapsed_ms=round((time.perf_counter() - start) * 1000, 2)))
    return dict(scope=manifest['scope'], input_manifest_sha256=hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
                evaluator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                unique_input_files=len(assets), tested_workflows=len(results),
                passed=sum(item['passed'] for item in results), cases=results,
                timing_scope='Local in-process test client, not mobile/network latency')


if __name__ == '__main__':
    result = evaluate()
    target = ROOT / 'experiments/demo-alternative-results.json'
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{result["passed"]}/{result["tested_workflows"]} offline substitution checks passed')
    if result['passed'] != result['tested_workflows']:
        raise SystemExit(1)
