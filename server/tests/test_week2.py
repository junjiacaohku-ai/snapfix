import json
from pathlib import Path
import sqlite3
import uuid

from fastapi.testclient import TestClient
import pytest
import main as api
from corpus_store import import_corpus
from retrieval import Retriever
from retrieval_service import clear_retrieval_cache
from session_store import SessionStore
import report_service
DATA = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture
def client(tmp_path, monkeypatch):
    database = tmp_path / "test.db"
    import_corpus(database, DATA)
    store = SessionStore(database, api.Session.model_validate)
    monkeypatch.setattr(api, "DB", store)
    clear_retrieval_cache()
    with TestClient(api.app) as c:
        yield c
    clear_retrieval_cache()


def test_search_top3_and_exact_error_code(client):
    response = client.post("/api/manuals/search", json={
        "query": "博世 E:24 排水", "brand": "博世", "category": "dishwasher",
        "error_code": "E24", "limit": 3,
    })
    assert response.status_code == 200
    matches = response.json()["matches"]
    assert 1 <= len(matches) <= 3
    assert any(r["manual_id"] == "bosch-dishwasher-9001014024" and r["page"] == 35 for r in matches)
    assert all("score" in r and "source_url" in r for r in matches)
    result = client.post("/api/manuals/search", json={"query": "Bosch E999", "brand": "Bosch", "error_code": "E999"})
    assert result.status_code == 200 and result.json()["matches"] == []


def test_query_validation(client):
    assert client.post("/api/manuals/search", json={"query": "   "}).status_code == 422
    assert client.post("/api/manuals/search", json={"query": "E24", "limit": 0}).status_code == 422


def test_manual_endpoint_reads_real_candidates(client):
    r = client.post("/api/diagnose/manual", json={"brand": "博世", "error_code": "E:24"})
    assert r.status_code == 200
    session = r.json()
    assert session["device_category"] == "dishwasher"
    assert session["error_code"] == "E24"
    assert "35" in session["decision_reason"]
    assert session["steps"] == [] and session["decision"] == "professional"
    assert client.get("/api/sessions/" + session["id"]).json() == session


def test_unknown_code_does_not_fall_back_to_e24(client):
    r = client.post("/api/diagnose/manual", json={"brand": "Bosch", "error_code": "E999"})
    assert r.status_code == 200
    assert r.json()["error_code"] == "E999"
    assert "无可用引用" in r.json()["decision_reason"] and r.json()["steps"] == []


def test_dangerous_manual_request_is_refused(client):
    r = client.post("/api/diagnose/manual", json={"brand": "微波炉", "error_code": "不加热"})
    assert r.status_code == 200
    assert r.json()["safety_refused"] and r.json()["steps"] == []


def test_missing_database_is_not_reported_as_no_matches(client, monkeypatch, tmp_path):
    monkeypatch.setattr(api.DB, "path", tmp_path / "missing.db")
    assert client.post("/api/manuals/search", json={"query": "E24"}).status_code == 503


def test_empty_corpus_is_a_real_empty_result(client, tmp_path):
    folder = tmp_path / "empty"
    folder.mkdir()
    for name in ["manuals.json", "chunks.json"]:
        (folder/name).write_text("[]", encoding="utf-8")
    database = tmp_path / "empty.db"
    import_corpus(database, folder)
    from diagnosis_service import diagnose_manual_data
    data = diagnose_manual_data(database, "Bosch", "E24")
    assert data["device_category"] == "unknown" and "未找到" in data["decision_reason"]


def test_report_contents_persist_and_delete_cascades(client, monkeypatch):
    monkeypatch.setattr(
        report_service,
        "translate_texts",
        lambda texts, lang: list(texts),
    )
    # A synthetic record isolates report behavior from any unverified repair instructions.
    session = api.Session(
        id=str(uuid.uuid4()), device_category="router", brand="TP-Link", model="test-model",
        error_code=None, decision="professional", decision_reason="Test record",
        steps=[api.Step(id=str(uuid.uuid4()), idx=1, content="Recorded observation",
                       citation_manual="Test fixture", citation_section="test"),
               api.Step(id=str(uuid.uuid4()), idx=2, content="Skipped action",
                       citation_manual="Test fixture", citation_section="test", feedback="skipped")],
        created_at="2026-10-31T00:00:00+00:00",
    )
    api.DB[session.id] = session
    path = "/api/sessions/" + session.id
    assert client.post(path + "/steps/" + session.steps[0].id + "/feedback", json={"feedback":"done"}).status_code == 200
    for lang in ["zh", "en"]:
        r = client.post(path + "/report", json={"lang":lang, "photo_refs":["router-front.jpg"]})
        assert r.status_code == 200
        content = r.json()["content"]
        assert "Recorded observation" in content and "Skipped action" not in content
        assert "test-model" in content and "router-front.jpg" in content
    assert client.post(path + "/report", json={"lang":"fr"}).status_code == 422
    assert client.post(path + "/steps/" + session.steps[0].id + "/feedback", json={"feedback":"bad"}).status_code == 422
    reopened = SessionStore(api.DB.path, api.Session.model_validate)
    assert reopened[session.id].steps[0].feedback == "done"
    with reopened.connection() as db:
        assert db.execute("SELECT COUNT(*) FROM reports WHERE session_id=?", (session.id,)).fetchone()[0] == 2
    assert client.delete(path).status_code == 200
    assert client.get(path).status_code == 404
    with reopened.connection() as db:
        for table in ["steps", "reports"]:
            assert db.execute(f"SELECT COUNT(*) FROM {table} WHERE session_id=?", (session.id,)).fetchone()[0] == 0


def test_reference_retriever_keeps_confirmed_filters():
    def row(id_, text, category):
        return dict(id=id_, content=text, manual_id=id_, brand="Test", device_category=category)
    rows = [row("a", "E240 drain issue", "dishwasher"),
            row("b", "E24 drain issue", "dishwasher"),
            row("c", "E24 drain issue", "router")]
    found = Retriever(rows).search("drain E24", category="dishwasher", error_code="E24")
    assert [r["id"] for r in found] == ["b"]


@pytest.mark.parametrize("lang", ["zh", "en"])
def test_report_without_key_still_saves(client, monkeypatch, lang):
    import translation_service

    monkeypatch.setenv("GEMINI_API_KEY", "")
    network_calls = []

    def forbid_network(*args, **kwargs):
        network_calls.append(True)
        raise AssertionError("没有密钥时不应调用 Gemini 客户端")

    monkeypatch.setattr(
        translation_service.genai,
        "Client",
        forbid_network,
    )

    session = api._mock_e24()
    session.steps[0].feedback = "done"
    api.DB[session.id] = session

    response = client.post(
        f"/api/sessions/{session.id}/report",
        json={
            "lang": lang,
            "photo_refs": ["bosch-dishwasher-1.jpg"],
        },
    )

    assert response.status_code == 200
    assert network_calls == []
    content = response.json()["content"]
    assert "Bosch" in content
    assert "E24" in content
    assert "bosch-dishwasher-1.jpg" in content

    if lang == "en":
        assert "Step 1 (marked complete)." in content
        assert "Step descriptions were not translated." in content
    else:
        assert session.steps[0].content in content

    with api.DB.connection() as db:
        row = db.execute(
            "SELECT lang, content FROM reports WHERE session_id=?",
            (session.id,),
        ).fetchone()

    assert row["lang"] == lang
    assert row["content"] == content


def test_report_translation_failure_still_saves(client, monkeypatch):
    from translation_service import TranslationError

    def fail_translation(*args, **kwargs):
        raise TranslationError("Simulated service failure")

    monkeypatch.setattr(
        report_service,
        "translate_texts",
        fail_translation,
    )

    session = api._mock_e24()
    session.steps[0].feedback = "done"
    api.DB[session.id] = session

    response = client.post(
        f"/api/sessions/{session.id}/report",
        json={"lang": "en"},
    )

    assert response.status_code == 200
    content = response.json()["content"]
    assert "Step 1 (marked complete)." in content

    with api.DB.connection() as db:
        saved = db.execute(
            "SELECT content FROM reports WHERE session_id=?",
            (session.id,),
        ).fetchone()

    assert saved["content"] == content
