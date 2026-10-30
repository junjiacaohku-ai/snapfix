"""Run D-line labels against an explicitly selected BE-1 safety_gate.py revision."""
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path


def evaluate(gate_path, revision, cases):
    spec = importlib.util.spec_from_file_location('audited_safety_gate', gate_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    results = []
    for case in cases:
        verdict = module.check(case['text'])
        results.append({**case, 'actual_refused': verdict.refused,
                        'matched_category': verdict.category,
                        'passed': verdict.refused == case['expected_refused']})
    high = [r for r in results if r['expected_refused']]
    normal = [r for r in results if not r['expected_refused']]
    return dict(target_revision=revision, target_sha256=hashlib.sha256(gate_path.read_bytes()).hexdigest(),
                high_risk_recall=sum(r['actual_refused'] for r in high)/len(high),
                normal_false_positive_rate=sum(r['actual_refused'] for r in normal)/len(normal),
                total=len(results), passed=sum(r['passed'] for r in results), cases=results,
                scope='Unit evaluation of referenced gate, not integrated API/vision validation')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gate', type=Path, required=True)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    cases = json.loads((Path(__file__).resolve().parents[1]/'data/safety-evaluation-cases.json').read_text())
    report = evaluate(args.gate, args.revision, cases)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='cases'}, ensure_ascii=False))
    sys.exit(0 if report['passed']==report['total'] else 1)
