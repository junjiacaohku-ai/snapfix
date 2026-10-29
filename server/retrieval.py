"""D-line reference retriever for BE-2 integration; never generates repair steps."""
import re
import unicodedata
from rank_bm25 import BM25Okapi

ALIASES = {'博世': 'bosch', '普联': 'tp-link', 'tplink': 'tp-link', '宜家': 'ikea', '松下': 'panasonic'}
EXPANSIONS = {'排水': 'drain drainage waste water', '橙灯': 'orange led', '红灯': 'led internet',
              '断网': 'internet connection', '重启': 'reboot restart', '防倾倒': 'tip over wall',
              '墙体固定': 'wall attachment', '螺丝': 'screws', '微波炉': 'microwave',
              '不加热': 'not heating', '维修': 'repair', '专业人员': 'qualified technician',
              '燃气': 'gas', '热水器': 'water heater', '漏气': 'leak'}


def normalize_brand(value):
    value = unicodedata.normalize('NFKC', value or '').strip().lower()
    return ALIASES.get(value, value)


def tokens(value, expand=False):
    value = unicodedata.normalize('NFKC', value).lower()
    value = re.sub(r'\be\s*:\s*(\d+)\b', r'e\1', value)
    if expand:
        value += ' ' + ' '.join(v for k,v in EXPANSIONS.items() if k in value)
    return re.findall(r'[a-z0-9]+|[\u4e00-\u9fff]', value)


class Retriever:
    def __init__(self, rows):
        self.rows = rows
        self.words = [tokens(r['content']) for r in rows]
        self.index = BM25Okapi(self.words) if rows else None

    def search(self, query, *, category='', brand='', error_code='', manual_id='', limit=3):
        if not self.index or limit <= 0:
            return []
        query_words = tokens(query, expand=True)
        code = ''.join(tokens(error_code))
        if code and code not in query_words:
            query_words.append(code)
        scores = self.index.get_scores(query_words)
        result = []
        for row, words, score in zip(self.rows, self.words, scores):
            # A supplied model/manual is a verified upstream input, never an oracle label.
            if manual_id and row['manual_id'] != manual_id:
                continue
            if category and row['device_category'] != category:
                continue
            if brand and normalize_brand(row['brand']) != normalize_brand(brand):
                continue
            if code and code not in words:
                continue
            overlap = set(query_words) & set(words)
            if not overlap:
                continue
            score = float(score) + (5.0 if code else 0.0)
            result.append((score, row))
        result.sort(key=lambda pair: (-pair[0], pair[1]['id']))
        return [{**r, 'score': s} for s,r in result[:limit]]
