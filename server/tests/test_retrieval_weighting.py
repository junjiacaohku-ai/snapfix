import pytest

from retrieval import Retriever


def make_row(id_, content, category="dishwasher"):
    return {
        "id": id_,
        "manual_id": id_,
        "brand": "Bosch",
        "device_category": category,
        "content": content,
    }


def test_category_hint_changes_order_without_filtering():
    rows = [
        make_row("a", "internet connection", "other"),
        make_row("b", "internet connection", "router"),
    ]
    retriever = Retriever(rows)
    baseline = retriever.search("internet connection")
    weighted = retriever.search(
        "internet connection", category_hint="router",
    )
    assert [row["id"] for row in baseline] == ["a", "b"]
    assert [row["id"] for row in weighted] == ["b", "a"]
    assert weighted[0]["score_detail"]["category_bonus"] == pytest.approx(3.0)


def test_confirmed_category_still_filters():
    rows = [
        make_row("a", "internet connection", "other"),
        make_row("b", "internet connection", "router"),
    ]
    results = Retriever(rows).search(
        "internet connection", category="router", category_hint="other",
    )
    assert [row["id"] for row in results] == ["b"]


def test_error_code_weight_changes_order():
    rows = [
        make_row("a", "E24 drain drain drain blockage blockage blockage note"),
        make_row("b", "E24 E24 E24 drain blockage note filler filler"),
    ]
    rows += [
        make_row(
            f"other-{index}",
            "general user manual setup power settings notes information",
        )
        for index in range(6)
    ]
    baseline = Retriever(rows, error_code_weight=1).search(
        "drain blockage E24", error_code="E24",
    )
    weighted = Retriever(rows, error_code_weight=3).search(
        "drain blockage E24", error_code="E24",
    )
    assert baseline[0]["id"] == "a"
    assert weighted[0]["id"] == "b"
    for row in weighted:
        detail = row["score_detail"]
        expected = (
            detail["base_bm25"]
            + detail["category_bonus"]
            + detail["error_code_extra"]
        )
        assert row["score"] == pytest.approx(expected)


def test_weighting_does_not_bypass_exact_code_or_relevance():
    rows = [
        make_row("a", "E240 drain issue"),
        make_row("b", "E24 drain issue"),
    ]
    retriever = Retriever(rows)
    results = retriever.search(
        "E24 drain", error_code="E24", category_hint="dishwasher",
    )
    assert [row["id"] for row in results] == ["b"]
    assert retriever.search(
        "unrelatedxyz", category_hint="dishwasher",
    ) == []
