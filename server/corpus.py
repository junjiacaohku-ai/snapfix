"""Offline manual ETL; JSON contract for BE-2 ingestion."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def chunks(text, size=500):
    if size < 1:
        raise ValueError('size must be positive')
    text = re.sub(r'[ \t]+', ' ', text.replace('\x00', '')).strip()
    for start in range(0, len(text), size):
        yield text[start:start + size]


def extract(path, metadata):
    import pdfplumber
    result = []
    with pdfplumber.open(path) as pdf:
        section = 'unclassified'
        for page_number, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ''
            if '(cid:' in text:
                import pymupdf
                with pymupdf.open(path) as fallback:
                    text = fallback[page_number - 1].get_text()
                if '(cid:' in text or not text.strip():
                    raise ValueError(f'{path}: page {page_number} has undecoded font glyphs; OCR required')
            # Keep numbered headings with their paragraphs; never invent sections.
            parts = re.split(r'(?m)^(?=\s*(?:Chapter\s+\d+|\d+(?:\.\d+)*[.)]?\s+[A-Za-z]|第[一二三四五六七八九十0-9]+[章节]))', text)
            page_chunks = []
            for part in parts:
                heading = part.strip().split('\n', 1)[0] if part.strip() else ''
                if re.match(r'^(?:Chapter\s+\d+|\d+(?:\.\d+)*[.)]?\s+[A-Za-z]|第[一二三四五六七八九十0-9]+[章节])', heading):
                    section = heading[:160]
                page_chunks.extend((content, section) for content in chunks(part))
            for index, (content, section_name) in enumerate(page_chunks):
                key = f'{metadata["source_url"]}:{page_number}:{index}:{content}'
                result.append({**metadata, 'id': hashlib.sha256(key.encode()).hexdigest()[:24],
                               'page': page_number, 'section': section_name,
                               'content': content})
    if not result:
        raise ValueError(f'{path}: no extractable text; OCR required')
    return result


def weighted_matches(rows, query, category='', brand='', error_code=''):
    """Lexical baseline for BE-2; metadata boosts, not a BM25 replacement."""
    aliases = {'博世': 'bosch', '普联': 'tp-link'}
    brand = aliases.get(brand.lower(), brand.lower())
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    rows = []
    for record in json.loads(args.manifest.read_text()):
        record = dict(record)
        path = args.manifest.parent / record.pop('file')
        rows.extend(extract(path, record))
    args.output.write_text(json.dumps(rows, ensure_ascii=False, indent=2))
