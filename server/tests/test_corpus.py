from corpus import chunks, weighted_matches


def test_chunks_preserve_content_and_bound_size():
    text = '中文说明书。' * 200
    result = list(chunks(text))
    assert ''.join(result) == text
    assert all(len(part) <= 500 for part in result)


def test_error_code_exact_and_brand_alias():
    rows = [{'content': 'E240 other', 'brand': 'Other'},
            {'content': 'E24 drain', 'brand': 'Bosch'}]
    assert weighted_matches(rows, '', brand='博世', error_code='E24') == [rows[1]]


def test_real_manual_provenance_and_stable_ids():
    import json
    from pathlib import Path
    from corpus import extract
    root = Path(__file__).resolve().parents[1] / 'data'
    metadata = dict(json.loads((root / 'manifest.json').read_text())[2])
    file = root / metadata.pop('file')
    first = extract(file, metadata)
    second = extract(file, metadata)
    assert first == second
    assert first and all(row['source_url'] and row['page'] > 0 for row in first)
    assert all(len(row['content']) <= 500 for row in first)
    assert len({row['id'] for row in first}) == len(first)


def test_undecoded_font_manual_fallback():
    import json
    from pathlib import Path
    from corpus import extract
    root = Path(__file__).resolve().parents[1] / 'data'
    metadata = dict(json.loads((root / 'manifest.json').read_text())[0])
    path = root / metadata.pop('file')
    rows = extract(path, metadata)
    assert rows and all('(cid:' not in r['content'] for r in rows)
    assert any('washing' in r['content'].lower() for r in rows)


def test_visual_correction_is_source_bound():
    import json
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]/'data'
    rows = json.loads((root/'chunks.json').read_text())
    e24 = [r for r in rows if r['manual_id']=='bosch-dishwasher-9001014024' and 'E:24' in r['content']]
    assert e24 and all(r['page']==35 and r['visual_correction'] for r in e24)
