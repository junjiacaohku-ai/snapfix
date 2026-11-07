"""Check fixed degradations through both the pixel gate and upload endpoint."""
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.build_quality_variants import ASSETS, OUTPUT, sha256
from image_quality import check_image


def evaluate(client, output=OUTPUT):
    output = Path(output)
    manifest = json.loads((output/'manifest.json').read_text())
    if manifest['detector_sha256'] != sha256((ROOT/'image_quality.py').read_bytes()):
        raise ValueError('detector changed; rebuild variants and identify the new experiment')
    results = []
    for original in manifest['originals']:
        inputs = [dict(file=original['source_file'], kind='original', sha256=original['source_sha256'])]
        inputs += original['variants']
        for item in inputs:
            path = (ASSETS if item['kind']=='original' else output)/item['file']
            data = path.read_bytes()
            if sha256(data) != item['sha256']:
                raise ValueError(f'input changed: {path.name}')
            verdict = check_image(data).to_dict()
            # All uploads use the same mock scenario name, including the dark/blur PNGs.
            mime = 'image/jpeg' if item['kind']=='original' else 'image/png'
            response = client.post('/api/analyze/image', files={'file':('router.jpg',data,mime)})
            if item['kind']=='original':
                treatment_passed = None
            elif item['kind']=='dark':
                treatment_passed = not verdict['accepted'] and '过暗' in verdict['reason']
            elif item['blur_only_eligible']:
                treatment_passed = not verdict['accepted'] and '细节' in verdict['reason']
            else:
                treatment_passed = not verdict['accepted']  # Already dark: not a blur-only success.
            expected_status = 200 if verdict['accepted'] else 422
            api_passed = response.status_code==expected_status
            if not verdict['accepted']:
                api_passed = api_passed and response.json().get('detail')==verdict['reason']
            results.append({**item, 'source_file':original['source_file'],
                            'source_family':original['source_family'], **verdict,
                            'treatment_passed':treatment_passed, 'api_status':response.status_code,
                            'api_passed':api_passed})
    originals = [r for r in results if r['kind']=='original']
    dark = [r for r in results if r['kind']=='dark']
    blur = [r for r in results if r['kind']=='blur' and r['blur_only_eligible']]
    mixed = [r for r in results if r['kind']=='blur' and not r['blur_only_eligible']]
    return dict(
        manifest_sha256=sha256((output/'manifest.json').read_bytes()),
        detector_sha256=manifest['detector_sha256'], parameters=manifest['parameters'],
        unique_originals=len(originals), source_families=manifest['source_families'],
        original_accepted=sum(r['accepted'] for r in originals), original_retake=sum(not r['accepted'] for r in originals),
        dark={'cases':len(dark), 'correct_retake':sum(r['treatment_passed'] for r in dark)},
        blur_only={'cases':len(blur), 'correct_retake':sum(r['treatment_passed'] for r in blur)},
        already_dark_blurred={'cases':len(mixed), 'retake':sum(not r['accepted'] for r in mixed),
                              'counted_as_blur_only':False},
        api={'cases':len(results), 'passed':sum(r['api_passed'] for r in results), 'upload_name':'router.jpg'},
        all_checks_passed=all(r['api_passed'] and r['treatment_passed'] is not False for r in results),
        scope='Synthetic severe-degradation regression, not phone-camera accuracy or device recognition', cases=results)


if __name__ == '__main__':
    from fastapi.testclient import TestClient
    with TemporaryDirectory(prefix='snapfix-quality-') as directory:
        os.environ['SNAPFIX_DB'] = str(Path(directory)/'quality.db')
        from main import app
        with TestClient(app) as client:
            report = evaluate(client)
    (ROOT/'experiments/quality-variant-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='cases'},ensure_ascii=False))
    if not report['all_checks_passed']:
        raise SystemExit(1)
