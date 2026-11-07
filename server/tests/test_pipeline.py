from pathlib import Path

from fastapi.testclient import TestClient
import pytest

import main as api
from pipeline import diagnose_image
from providers import GeneratedDiagnosis, GeneratedStep, VisionResult


def vision(category="router", model="WR940N", confidence=0.9):
    return VisionResult(
        device_category=category,
        brand="TP-Link" if category == "router" else "Bosch",
        model=model,
        error_code=None,
        visible_faults=["指示灯异常"],
        confidence=confidence,
    )


def match():
    return {
        "id": "chunk-1",
        "title": "TP-Link WR940N User Guide",
        "manual_id": "tplink-wr940n",
        "page": 120,
        "content": "Check the external power and ethernet cable. Restart the router.",
        "device_category": "router",
        "brand": "TP-Link",
        "source_url": "https://example.com/manual",
    }


def generated(decision="diy"):
    return GeneratedDiagnosis(
        decision=decision,
        decision_reason="External checks are supported by the retrieved manual.",
        steps=[
            GeneratedStep(content="Check the external power and ethernet cable.", citation_chunk_id="chunk-1"),
            GeneratedStep(content="Invent a missing citation.", citation_chunk_id="missing"),
            GeneratedStep(content="配电箱带电维修", citation_chunk_id="chunk-1"),
        ],
    )


def test_pipeline_refuses_high_risk_before_retrieval():
    def forbidden_search(*args, **kwargs):
        raise AssertionError("retrieval must not run for a refused device")

    result = diagnose_image(
        b"image",
        "unused",
        vision_extract=lambda *args: vision("microwave", "HMT84"),
        generate=lambda *args: generated(),
        search=forbidden_search,
    )
    assert result["safety_refused"] and result["decision"] == "refused"
    assert result["steps"] == [] and result["source_mode"] == "gemini"


def test_pipeline_low_confidence_abstains():
    result = diagnose_image(
        b"image",
        "unused",
        vision_extract=lambda *args: vision(confidence=0.2),
        generate=lambda *args: generated(),
        search=lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("search must not run")),
    )
    assert result["decision"] == "professional" and result["steps"] == []
    assert "置信度较低" in result["decision_reason"]


def test_pipeline_empty_retrieval_has_explicit_no_citation():
    result = diagnose_image(
        b"image",
        "unused",
        vision_extract=lambda *args: vision(),
        generate=lambda *args: generated(),
        search=lambda *args, **kwargs: [],
    )
    assert result["decision"] == "professional" and result["steps"] == []
    assert "无可用引用" in result["decision_reason"]


def test_pipeline_drops_fake_and_dangerous_citations():
    result = diagnose_image(
        b"image",
        "unused",
        vision_extract=lambda *args: vision(),
        generate=lambda *args: generated(),
        search=lambda *args, **kwargs: [match()],
    )
    assert result["decision"] == "diy" and len(result["steps"]) == 1
    step = result["steps"][0]
    assert step["citation_manual"] == match()["title"]
    assert "chunk-1" in step["citation_section"]
    assert "Invent" not in step["content"] and "配电箱" not in step["content"]


def test_pipeline_requires_exact_model_for_diy():
    result = diagnose_image(
        b"image",
        "unused",
        vision_extract=lambda *args: vision(model=None),
        generate=lambda *args: generated(),
        search=lambda *args, **kwargs: [match()],
    )
    assert result["decision"] == "professional" and result["steps"] == []
    assert "完整型号" in result["decision_reason"]


def test_pipeline_generation_failure_returns_none():
    result = diagnose_image(
        b"image",
        "unused",
        vision_extract=lambda *args: vision(),
        generate=lambda *args: None,
        search=lambda *args, **kwargs: [match()],
    )
    assert result is None


def test_pipeline_retrieves_real_corpus(tmp_path):
    from corpus_store import import_corpus

    database = tmp_path / "corpus.db"
    import_corpus(database, Path(__file__).resolve().parents[1] / "data")
    seen = {}

    def generate(vision, matches):
        seen["matches"] = matches
        return GeneratedDiagnosis(
            decision="professional",
            decision_reason="Candidate manual found; exact model still needs confirmation.",
            steps=[],
        )

    result = diagnose_image(
        b"image",
        database,
        vision_extract=lambda *args: VisionResult(
            device_category="dishwasher",
            brand="Bosch",
            model="SM/SB",
            error_code="E:24",
            visible_faults=["排水异常"],
            confidence=0.9,
        ),
        generate=generate,
    )
    assert result["source_mode"] == "gemini"
    assert any(row["manual_id"] == "bosch-dishwasher-9001014024" and row["page"] == 35 for row in seen["matches"])


def live_payload():
    return {
        "id": "live-session",
        "device_category": "router",
        "brand": "TP-Link",
        "model": "WR940N",
        "error_code": None,
        "decision": "professional",
        "decision_reason": "Live test result",
        "steps": [],
        "safety_refused": False,
        "created_at": "2026-11-07T00:00:00+00:00",
        "source_mode": "gemini",
    }


def image_bytes():
    return (Path(__file__).resolve().parents[2] / "docs/demo-assets/public/public-01.jpg").read_bytes()


def test_analyze_image_uses_live_pipeline_when_enabled(monkeypatch):
    monkeypatch.setattr(api, "MOCK_MODE", False)
    monkeypatch.setattr(api, "diagnose_image", lambda *args: live_payload())
    with TestClient(api.app) as client:
        response = client.post(
            "/api/analyze/image",
            files={"file": ("anything.jpg", image_bytes(), "image/jpeg")},
        )
    assert response.status_code == 200
    assert response.json()["source_mode"] == "gemini"
    assert response.json()["id"] == "live-session"


def test_analyze_image_falls_back_to_labeled_mock(monkeypatch):
    monkeypatch.setattr(api, "MOCK_MODE", False)
    monkeypatch.setattr(api, "diagnose_image", lambda *args: None)
    with TestClient(api.app) as client:
        response = client.post(
            "/api/analyze/image",
            files={"file": ("router.jpg", image_bytes(), "image/jpeg")},
        )
    assert response.status_code == 200
    assert response.json()["source_mode"] == "mock"
    assert response.json()["brand"] == "TP-Link"


@pytest.mark.parametrize("forced,key,expected", [
    ("1", "configured", True),
    ("0", "configured", False),
    ("0", "", True),
    ("", "", True),
])
def test_mock_mode_switch(monkeypatch, forced, key, expected):
    monkeypatch.setenv("SNAPFIX_MOCK", forced)
    monkeypatch.setenv("GEMINI_API_KEY", key)
    assert api._mock_mode() is expected
