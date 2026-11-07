"""BE-2 retriever based on the D-line reference implementation."""

import math
import re
import unicodedata

from rank_bm25 import BM25Okapi


ALIASES = {
    "博世": "bosch",
    "普联": "tp-link",
    "tplink": "tp-link",
    "宜家": "ikea",
    "松下": "panasonic",
}

CATEGORY_ALIASES = {
    "ikea_furniture": "furniture",
}

EXPANSIONS = {
    "排水": "drain drainage waste water",
    "橙灯": "orange led",
    "红灯": "led internet",
    "断网": "internet connection",
    "重启": "reboot restart",
    "防倾倒": "tip over wall",
    "墙体固定": "wall attachment",
    "螺丝": "screws",
    "微波炉": "microwave",
    "不加热": "not heating",
    "维修": "repair",
    "专业人员": "qualified technician",
    "燃气": "gas",
    "热水器": "water heater",
    "漏气": "leak",
}


def normalize_brand(value):
    value = unicodedata.normalize("NFKC", value or "").strip().lower()
    return ALIASES.get(value, value)


def normalize_category(value):
    value = unicodedata.normalize("NFKC", value or "").strip().lower()
    return CATEGORY_ALIASES.get(value, value)


def tokens(value, expand=False):
    value = unicodedata.normalize("NFKC", value).lower()
    value = re.sub(r"\be\s*:\s*(\d+)\b", r"e\1", value)
    if expand:
        value += " " + " ".join(
            translation
            for word, translation in EXPANSIONS.items()
            if word in value
        )
    return re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", value)


class Retriever:
    def __init__(self, rows, *, category_weight=3.0, error_code_weight=3.0):
        self.category_weight = float(category_weight)
        self.error_code_weight = float(error_code_weight)
        if not math.isfinite(self.category_weight) or self.category_weight < 0:
            raise ValueError("category_weight must be finite and >= 0")
        if not math.isfinite(self.error_code_weight) or self.error_code_weight < 1:
            raise ValueError("error_code_weight must be finite and >= 1")
        self.rows = rows
        self.words = [tokens(row["content"]) for row in rows]
        self.index = BM25Okapi(self.words) if rows else None

    def search(
        self,
        query,
        *,
        category="",
        category_hint="",
        brand="",
        error_code="",
        manual_id="",
        limit=3,
    ):
        if not self.index or limit <= 0 or not query.strip():
            return []
        category = normalize_category(category)
        category_hint = normalize_category(category_hint)
        brand = normalize_brand(brand)
        query_words = tokens(query, expand=True)
        code = "".join(tokens(error_code))
        if code:
            query_words = [word for word in query_words if word != code]
            query_words.append(code)
        base_scores = self.index.get_scores(query_words)
        code_scores = self.index.get_scores([code]) if code else [0.0] * len(self.rows)
        results = []
        for row, words, base, code_score in zip(
            self.rows, self.words, base_scores, code_scores,
        ):
            row_category = normalize_category(row.get("device_category", ""))
            if manual_id and row["manual_id"] != manual_id:
                continue
            if category and row_category != category:
                continue
            if brand and normalize_brand(row.get("brand", "")) != brand:
                continue
            if code and code not in words:
                continue
            if not set(query_words).intersection(words):
                continue
            category_bonus = (
                self.category_weight
                if category_hint and row_category == category_hint
                else 0.0
            )
            error_code_extra = (self.error_code_weight - 1) * float(code_score)
            score = float(base) + category_bonus + error_code_extra
            results.append({
                **row,
                "score": score,
                "score_detail": {
                    "base_bm25": float(base),
                    "category_bonus": category_bonus,
                    "error_code_extra": error_code_extra,
                },
            })
        results.sort(key=lambda row: (-row["score"], row["id"]))
        return results[:limit]
