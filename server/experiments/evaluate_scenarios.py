"""Six-scenario evidence table. Bypass workflows are not counted as retrieval successes."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from retrieval import Retriever

ROOT = Path(__file__).resolve().parents[1]
CASES = [
    dict(id='S1', kind='retrieval', query='TP-Link orange LED internet connection', category='router', brand='TP-Link', expected_manual='tplink-wr940n', pages=[8]),
    dict(id='S2', kind='retrieval', query='博世 E:24 排水', category='dishwasher', brand='博世', error_code='E:24', expected_manual='bosch-dishwasher-9001014024', pages=[35]),
    dict(id='S3', kind='retrieval', query='BILLY wall attachment tip over', category='furniture', brand='IKEA', manual_id='billy', expected_manual='billy', pages=[2], assumption='AA-2289105-4 explicitly chosen demo manual, not recognized from image'),
    dict(id='S4', kind='safety_reference', query='微波炉 修理 禁止分解', category='microwave', brand='Panasonic', expected_manual='panasonic-gm333w', pages=[3], assumption='Safety evidence lookup only; production must refuse before generating repair steps'),
    dict(id='S5', kind='quality_bypass', expected='retake image; no retrieval', status='Pixel-quality gate verified in acceptance-results.json and quality-variant-results.json; mobile retake UI still pending'),
    dict(id='S6', kind='report_bypass', expected='report from saved diagnosis and feedback; no new retrieval', status='Reports and feedback persist in SQLite; verified in server-check.json; photo attachment and App sharing still pending'),
]
NEGATIVES = [
    dict(id='N1', query='E240 drain', category='dishwasher', brand='Bosch', error_code='E240'),
    dict(id='N2', query='E999', error_code='E999'),
    dict(id='N3', query='internet', manual_id='missing-manual'),
    dict(id='N4', query='zqxwunrelatedtoken'),
]


def run():
    rows = json.loads((ROOT/'data/chunks.json').read_text())
    retriever = Retriever(rows)
    results = []
    for case in CASES + NEGATIVES:
        if case.get('kind','') in {'quality_bypass', 'report_bypass'}:
            results.append(case)
            continue
        options = {k:case[k] for k in ['category','brand','error_code','manual_id'] if k in case}
        hits = retriever.search(case['query'], **options)
        passed = (not hits if case['id'].startswith('N') else
                  any(r['manual_id']==case['expected_manual'] and r['page'] in case['pages'] for r in hits))
        results.append({**case,'passed':passed,'top3':[{k:r[k] for k in ['id','manual_id','page','score']} for r in hits]})
    report = dict(scope='4 evidence retrievals, 2 retrieval-bypass workflows, 4 abstention controls; not 6/6 live end-to-end', cases=results)
    (ROOT/'experiments/scenario-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if any(not r.get("passed", True) for r in results):
        raise SystemExit(1)


if __name__=='__main__':
    run()
