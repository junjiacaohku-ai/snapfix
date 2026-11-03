from pathlib import Path

import pytest

from corpus_store import import_corpus, read_chunks
from retrieval import Retriever


DATA = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture(scope="module")
def retriever(tmp_path_factory):
    database = tmp_path_factory.mktemp("be2-corpus") / "test.db"
    import_corpus(database, DATA)
    return Retriever(read_chunks(database))


@pytest.mark.parametrize(
    "query, options, should_match",
    [
        ("Bosch E24", {"brand": "Bosch", "category": "dishwasher",
                       "error_code": "E24"}, True),
        ("博世 E:24 排水", {"brand": "博世", "category": "dishwasher",
                            "error_code": "E:24"}, True),
        ("Bosch E999", {"brand": "Bosch", "error_code": "E999"}, False),
        ("Bosch E240", {"brand": "Bosch", "error_code": "E240"}, False),
        ("Bosch E24", {"brand": "Bosch", "category": "router",
                       "error_code": "E24"}, False),
        ("Bosch E24", {"brand": "Bosch", "error_code": "E24",
                       "manual_id": "nonexistent-manual"}, False),
    ],
    ids=["english-e24", "chinese-alias", "unknown-code",
         "e240-not-e24", "wrong-category", "unknown-manual"],
)
def test_real_corpus_search_contract(retriever, query, options, should_match):
    results = retriever.search(query, limit=3, **options)

    if not should_match:
        assert results == []
        return

    assert 1 <= len(results) <= 3
    assert any(
        row["manual_id"] == "bosch-dishwasher-9001014024"
        and row["page"] == 35
        for row in results
    )
    for row in results:
        assert row["text"] == row["content"]
        assert row["source_url"].startswith("https://")
        assert row["title"] and row["id"]
        assert isinstance(row["page"], int)
        assert isinstance(row["score"], float)