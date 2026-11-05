from functools import lru_cache
from pathlib import Path

from corpus_store import read_chunks
from retrieval import Retriever


@lru_cache(maxsize=4)
def _get_retriever(database: str) -> Retriever:
    return Retriever(read_chunks(database))


def search_manuals(
    database,
    query: str,
    *,
    category: str = "",
    category_hint: str = "",
    brand: str = "",
    error_code: str = "",
    manual_id: str = "",
    limit: int = 3,
):
    if not query.strip():
        return []
    path = str(Path(database).resolve())
    return _get_retriever(path).search(
        query,
        category=category,
        category_hint=category_hint,
        brand=brand,
        error_code=error_code,
        manual_id=manual_id,
        limit=limit,
    )


def clear_retrieval_cache():
    _get_retriever.cache_clear()
