from types import SimpleNamespace

import pytest

import report_service
import translation_service
from translation_service import (
    TranslatedItem,
    TranslationBatch,
    TranslationError,
)


def test_english_report_uses_translated_completed_steps(monkeypatch):
    session = SimpleNamespace(
        device_category="router",
        brand="TP-Link",
        model="test-model",
        error_code=None,
        steps=[
            SimpleNamespace(
                idx=1,
                content="已记录指示灯状态。",
                feedback="done",
            ),
            SimpleNamespace(
                idx=2,
                content="联系售后。",
                feedback="skipped",
            ),
        ],
    )

    def fake_translate(texts, lang):
        assert lang == "en"
        assert texts == ["router", "已记录指示灯状态。"]
        return ["router", "Recorded the indicator light status."]

    monkeypatch.setattr(
        report_service,
        "translate_texts",
        fake_translate,
    )

    result = report_service.build_report(
        session,
        "en",
        ["router-front.jpg"],
    )

    assert "Recorded the indicator light status." in result
    assert "已记录指示灯状态。" not in result
    assert "联系售后。" not in result
    assert "test-model" in result
    assert "router-front.jpg" in result
    assert session.steps[0].content == "已记录指示灯状态。"


def test_translation_restores_original_order(monkeypatch):
    monkeypatch.setattr(
        translation_service,
        "_request_translation",
        lambda texts, lang: TranslationBatch(items=[
            TranslatedItem(index=1, text="Second"),
            TranslatedItem(index=0, text="First"),
        ]),
    )

    assert translation_service.translate_texts(
        ["第一", "第二"], "en"
    ) == ["First", "Second"]


def test_missing_translation_is_rejected(monkeypatch):
    monkeypatch.setattr(
        translation_service,
        "_request_translation",
        lambda texts, lang: TranslationBatch(items=[
            TranslatedItem(index=0, text="First"),
        ]),
    )

    with pytest.raises(TranslationError):
        translation_service.translate_texts(
            ["第一", "第二"], "en"
        )