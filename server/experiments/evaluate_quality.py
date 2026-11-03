"""Measure the existing public photographs without altering them."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from image_quality import check_image


def run():
    assets = ROOT.parent / 'docs/demo-assets/public'
    sources = json.loads((assets/'sources.json').read_text())
    seen, results = set(), []
    for source in sources:
        if not source['file'].endswith('.jpg'):
            continue
        data = (assets/source['file']).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        results.append(dict(file=source['file'], sha256=digest, source=source['page'],
                            **check_image(data).to_dict()))
    report = dict(unique_originals=len(results), accepted=sum(r['accepted'] for r in results),
                  retake=sum(not r['accepted'] for r in results),
                  scope='Measurements of unchanged public photos; not a labelled accuracy benchmark',
                  cases=results)
    (ROOT/'experiments/quality-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='cases'}))


if __name__ == '__main__':
    run()
