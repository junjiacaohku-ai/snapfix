"""Replay the six offline flows in an isolated database on either demo computer."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
from tempfile import TemporaryDirectory
import time

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
MANIFEST = REPO / 'docs/demo-assets/demo-manifest.json'
sys.path.insert(0, str(ROOT))


def read_cases(path):
    manifest = json.loads(path.read_text(encoding='utf-8'))
    cases = manifest['cases']
    if [case['id'] for case in cases] != [f'S{i}' for i in range(1, 7)]:
        raise ValueError('Expected S1 through S6 once each, in order')
    for case in cases:
        if case['input_kind'] == 'image':
            source = (REPO / case['source_file']).resolve()
            if not source.is_relative_to(REPO.resolve()):
                raise ValueError('Image must be inside the repository')
            if hashlib.sha256(source.read_bytes()).hexdigest() != case['sha256']:
                raise ValueError(f'Image checksum mismatch: {case["id"]}')
    return cases


def run(cases, label):
    # Set this before importing main; never open the user's regular database.
    with TemporaryDirectory(prefix='snapfix-acceptance-') as folder:
        os.environ['SNAPFIX_DB'] = str(Path(folder) / 'acceptance.db')
        from corpus_store import import_corpus
        from fastapi.testclient import TestClient
        from main import app

        import_corpus(os.environ['SNAPFIX_DB'], ROOT / 'data')

        results = []
        with TestClient(app) as client:
            health = client.get('/api/health')
            for case in cases:
                scenario = case['id']
                start = time.perf_counter()
                if case['input_kind'] == 'manual':
                    response = client.post('/api/diagnose/manual', json=case['payload'])
                else:
                    picture = (REPO / case['source_file']).read_bytes()
                    response = client.post('/api/analyze/image', files={
                        'file': (case['upload_name'], picture, 'image/jpeg')})
                data = response.json()
                reports = {}
                checks = {'http_status': response.status_code == (422 if scenario == 'S5' else 200)}
                if scenario == 'S1':
                    checks['router_steps'] = data.get('brand') == 'TP-Link' and bool(data.get('steps'))
                elif scenario == 'S2':
                    checks['model_uncertainty'] = data.get('model') is None
                    checks['e24_referral'] = (data.get('device_category') == 'dishwasher'
                        and data.get('decision') == 'professional' and data.get('error_code') == 'E24')
                elif scenario == 'S3':
                    checks['billy_guidance'] = data.get('brand') == 'IKEA' and '防倾倒' in str(data.get('steps'))
                elif scenario == 'S4':
                    checks['refusal'] = data.get('safety_refused') is True and data.get('steps') == []
                elif scenario == 'S5':
                    checks['retake'] = '重拍' in data.get('detail', '')
                elif scenario == 'S6':
                    checks.update(feedback_saved=False, reports=False, report_status=False)
                    if response.status_code == 200 and data.get('steps'):
                        url = f'/api/sessions/{data["id"]}'
                        feedback = client.post(f'{url}/steps/{data["steps"][0]["id"]}/feedback',
                                               json={'feedback': 'done'})
                        saved = client.get(url)
                        checks['feedback_saved'] = (feedback.status_code == 200 and saved.status_code == 200
                            and saved.json()['steps'][0]['feedback'] == 'done')
                        report_responses = {lang: client.post(url + '/report', json={'lang': lang})
                                            for lang in ['zh', 'en']}
                        reports = {lang: item.json() for lang, item in report_responses.items()}
                        checks['report_status'] = all(item.status_code == 200 for item in report_responses.values())
                        checks['reports'] = ('步骤1' in reports['zh'].get('content', '')
                            and 'step 1' in reports['en'].get('content', '').lower()
                            and 'attach a photo' in reports['en'].get('content', ''))
                results.append(dict(scenario=scenario, title=case['title'],
                    input=case.get('upload_name', case.get('payload')),
                    source_file=case.get('source_file'), source_sha256=case.get('sha256'),
                    status=response.status_code, checks=checks, passed=all(checks.values()),
                    elapsed_ms=round((time.perf_counter() - start) * 1000, 2), response=data, reports=reports))
        return dict(scope='Offline backend only; no live vision or mobile UI coverage. '
                          'Timings use an in-process HTTP test client, not phone/network latency.',
                    machine_label=label, platform=platform.system(), python=platform.python_version(),
                    mock_health=health.status_code == 200 and health.json().get('mock') is True,
                    cases=results)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'experiments/acceptance-results.json')
    parser.add_argument('--label', default='local')
    parser.add_argument('--manifest', type=Path, default=MANIFEST)
    args = parser.parse_args()
    cases = read_cases(args.manifest)  # Reject damaged inputs before opening the application.
    result = run(cases, args.label)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    count = sum(case['passed'] for case in result['cases'])
    print(f'{count}/6 offline backend checks passed; mock health: {result["mock_health"]}')
    print(f'Results: {args.output}')
    if count != 6 or not result['mock_health']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
