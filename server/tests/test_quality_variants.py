import json
from fastapi.testclient import TestClient
from experiments.build_quality_variants import ASSETS, OUTPUT, build, sha256
from experiments.evaluate_quality_variants import evaluate
from main import app


def test_controlled_degradations_and_upload_endpoint():
    with TestClient(app) as client:
        result = evaluate(client)
    assert result['all_checks_passed']
    assert result['unique_originals'] == 13
    assert result['dark'] == {'cases':13, 'correct_retake':13}
    assert result['blur_only'] == {'cases':12, 'correct_retake':12}
    assert result['already_dark_blurred']['counted_as_blur_only'] is False
    assert result['api']['passed'] == result['api']['cases'] == 39


def test_transform_reproduction_and_source_preservation(tmp_path):
    committed = json.loads((OUTPUT/'manifest.json').read_text())
    originals_before = {r['source_file']:sha256((ASSETS/r['source_file']).read_bytes())
                        for r in committed['originals']}
    # Reproducibility is checked within the installed runtime, not across Pillow versions.
    first, second = build(tmp_path/'first'), build(tmp_path/'second')
    assert first == second
    for source in first['originals']:
        assert sha256((ASSETS/source['source_file']).read_bytes()) == originals_before[source['source_file']]
        for variant in source['variants']:
            a, b = tmp_path/'first'/variant['file'], tmp_path/'second'/variant['file']
            assert a.read_bytes() == b.read_bytes()
            assert sha256(a.read_bytes()) == variant['sha256']
    assert (tmp_path/'first/preview.png').read_bytes() == (tmp_path/'second/preview.png').read_bytes()
