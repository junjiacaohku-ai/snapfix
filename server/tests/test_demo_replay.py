"""Verify portable replay and that a damaged backup cannot silently pass."""
import json
import os
from pathlib import Path
import subprocess
import sys

SERVER = Path(__file__).resolve().parents[1]
SCRIPT = SERVER / 'experiments/run_acceptance.py'
MANIFEST = SERVER.parent / 'docs/demo-assets/demo-manifest.json'


def test_replay_works_outside_repo_and_preserves_existing_database(tmp_path):
    database = tmp_path / 'existing.db'
    database.write_bytes(b'Existing user data must remain untouched')
    result_path = tmp_path / 'result.json'
    result = subprocess.run([sys.executable, str(SCRIPT), '--output', str(result_path), '--label', 'backup'],
                            cwd=tmp_path, env={**os.environ, 'SNAPFIX_DB': str(database)},
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert database.read_bytes() == b'Existing user data must remain untouched'
    data = json.loads(result_path.read_text())
    assert data['machine_label'] == 'backup' and data['mock_health']
    assert len(data['cases']) == 6 and all(item['passed'] for item in data['cases'])
    assert data['cases'][-1]['checks']['feedback_saved']


def test_replay_rejects_corrupt_image_manifest(tmp_path):
    manifest = json.loads(MANIFEST.read_text())
    manifest['cases'][0]['sha256'] = '0' * 64
    bad = tmp_path / 'manifest.json'
    bad.write_text(json.dumps(manifest))
    output = tmp_path / 'result.json'
    result = subprocess.run([sys.executable, str(SCRIPT), '--manifest', str(bad), '--output', str(output)],
                            cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert result.returncode != 0 and 'checksum mismatch: S1' in result.stderr
    assert not output.exists()
