"""Offline PDF ETL with source/page provenance and a BE-2-compatible JSON export."""
import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path

import pdfplumber
import pypdfium2 as pdfium


SCHEMA_VERSION = 2
HEADING = re.compile(r'^(?:Chapter\s+\d+\b|\d+(?:\.\d+)+\.?\s+\D|第[一二三四五六七八九十0-9]+[章节])')


def clean_text(text):
    text = unicodedata.normalize('NFKC', text).replace('\r\n', '\n')
    text = ''.join(c for c in text if c in '\n\t' or not unicodedata.category(c).startswith('C'))
    return re.sub(r'[ \t]+', ' ', text).strip()


def chunks(text, size=500):
    """Bounded text segments. Keep line boundaries when possible; no hidden overlap."""
    if size < 1:
        raise ValueError('size must be positive')
    text = clean_text(text)
    while text:
        end = min(size, len(text))
        if end < len(text):
            boundary = text.rfind('\n', max(1, end // 2), end)
            if boundary != -1:
                end = boundary + 1
        yield text[:end]
        text = text[end:]


def extract(path, metadata, audit=None):
    """Scans/image-only pages are recorded, never silently represented as readable text."""
    required = ('title', 'source_url', 'brand', 'device_category')
    if any(not metadata.get(key) for key in required):
        raise ValueError(f'{path}: missing required metadata')
    source_hash = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    manual_id = metadata.get('manual_id') or hashlib.sha256(metadata['source_url'].encode()).hexdigest()[:16]
    result = []
    heading = None
    correction_file = Path(__file__).parent/'data/text-corrections.json'
    corrections = json.loads(correction_file.read_text()) if correction_file.exists() else []
    with pdfplumber.open(path) as pdf:
        for page_number, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ''
            extractor = 'pdfplumber'
            if '(cid:' in text or '\ufffd' in text:
                with pdfium.PdfDocument(str(path)) as fallback:
                    fp = fallback[page_number - 1]
                    tp = fp.get_textpage()
                    try:
                        text = tp.get_text_range()
                    finally:
                        tp.close()
                        fp.close()
                extractor = 'pdfium-font-fallback'
            applied = False
            for correction in corrections:
                if (correction['manual_id']==manual_id and correction['page']==page_number
                        and correction['source_sha256']==source_hash):
                    for old, new in correction['replacements'].items():
                        text = text.replace(old, new)
                    applied = True
            text = clean_text(text)
            if '(cid:' in text or '\ufffd' in text:
                if audit is not None:
                    audit.append(dict(manual_id=manual_id, page=page_number, chars=len(text), extractor=extractor, status='excluded_undecoded_glyphs'))
                continue
            page_status = 'text_extracted' if len(text) >= 40 else 'sparse_or_image_page'
            if audit is not None:
                audit.append(dict(manual_id=manual_id, page=page_number, chars=len(text),
                                  extractor=extractor, status=page_status, visual_correction=applied))
            # Numbered list items are not treated as section headings.
            sections = []
            current = []
            for line in text.splitlines():
                if HEADING.match(line.strip()) and len(line.strip()) <= 160:
                    if current:
                        sections.append(('\n'.join(current), heading))
                    heading = line.strip()
                    current = []
                current.append(line)
            if current:
                sections.append(('\n'.join(current), heading))
            for part, section in sections:
                for content in chunks(part):
                    idx = len(result)
                    key = f'{manual_id}:{source_hash}:{page_number}:{idx}:{content}'
                    result.append({**metadata, 'schema_version': SCHEMA_VERSION,
                                   'manual_id': manual_id, 'idx': idx,
                                   'id': hashlib.sha256(key.encode()).hexdigest()[:24],
                                   'page': page_number, 'section': section or f'PDF page {page_number}',
                                   'section_method': 'heading_heuristic' if section else 'page_fallback',
                                   'extractor': extractor, 'page_status': page_status, 'visual_correction': applied,
                                   'source_sha256': source_hash, 'content': content, 'text': content})
    if not result:
        raise ValueError(f'{path}: no extractable text; OCR required')
    return result


def weighted_matches(rows, query, category='', brand='', error_code=''):
    """Legacy lexical baseline retained for comparison, not the production retriever."""
    aliases = {'博世': 'bosch', '普联': 'tp-link'}
    brand = aliases.get(brand.strip().lower(), brand.strip().lower())
    terms = re.findall(r'\w+', query.lower())
    scored = []
    for row in rows:
        content = row['content'].lower()
        score = sum(content.count(term) for term in terms)
        score += 3 * bool(category and row.get('device_category') == category)
        score += 2 * bool(brand and aliases.get(row.get('brand', '').lower(), row.get('brand', '').lower()) == brand)
        score += 5 * bool(error_code and re.search(r'(?<!\w)' + re.escape(error_code.lower()) + r'(?!\w)', content))
        if score:
            scored.append((score, row))
    return [row for _, row in sorted(scored, key=lambda pair: -pair[0])]


def build(manifest, output):
    rows, audit, manuals = [], [], []
    for record in json.loads(manifest.read_text(encoding='utf-8')):
        metadata = dict(record)
        path = manifest.parent / metadata.pop('file')
        extracted = extract(path, metadata, audit)
        rows.extend(extracted)
        manuals.append(dict(id=extracted[0]['manual_id'], title=metadata['title'],
                            source=metadata['source_url'], category=metadata['device_category']))
    # Publish only after every input has parsed successfully.
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_suffix('.tmp')
    temp.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(output)
    output.with_name('extraction-audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    output.with_name('manuals.json').write_text(json.dumps(manuals, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    built = build(args.manifest, args.output)
    print(f'{len(built)} chunks exported; see extraction-audit.json for sparse pages')
