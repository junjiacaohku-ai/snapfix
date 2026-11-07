"""SnapFix FastAPI backend with offline demo flows and SQLite persistence."""
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, UploadFile
from pydantic import BaseModel, Field

from diagnosis_service import diagnose_manual_data
from image_quality import MAX_BYTES, check_image
from report_service import build_report
from retrieval_service import search_manuals
from safety_gate import check as check_safety
from session_store import SessionStore
from translation_service import TranslationError

app = FastAPI(title="SnapFix API", version="0.1.0")

# Gemini is currently used only for optional report translation, not image diagnosis.
MOCK_MODE = True


class Step(BaseModel):
    id: str
    idx: int
    content: str
    citation_manual: str
    citation_section: str
    feedback: str | None = None


class Session(BaseModel):
    id: str
    device_category: str
    brand: str | None = None
    model: str | None = None
    error_code: str | None = None
    decision: str
    decision_reason: str
    steps: list[Step] = []
    safety_refused: bool = False
    created_at: str


class ManualDiagnoseRequest(BaseModel):
    brand: str
    error_code: str


class FeedbackRequest(BaseModel):
    feedback: Literal["done", "not_useful", "skipped"]


class ReportRequest(BaseModel):
    lang: Literal["zh", "en"] = "zh"
    photo_refs: list[Annotated[str, Field(min_length=1, max_length=120)]] = Field(
        default_factory=list, max_length=5,
    )


class ManualSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    category: str = ""
    category_hint: str = ""
    brand: str = ""
    error_code: str = ""
    manual_id: str = ""
    limit: int = Field(default=3, ge=1, le=10)


DB = SessionStore(
    os.environ.get(
        "SNAPFIX_DB",
        str(Path(__file__).parent / "data" / "snapfix.db"),
    ),
    Session.model_validate,
)


def _apply_safety(session: Session) -> Session:
    verdict = check_safety(
        session.device_category,
        session.brand,
        session.model,
        session.error_code,
    )
    if verdict.refused:
        session.decision = "refused"
        session.decision_reason = verdict.reason + " " + verdict.advice
        session.safety_refused = True
        session.steps = []
    return session


def _mock_e24() -> Session:
    return Session(
        id=str(uuid.uuid4()),
        device_category="dishwasher",
        brand="Bosch",
        model=None,
        error_code="E24",
        decision="professional",
        decision_reason="Bosch E24 演示：洗碗机排水异常。请先核对完整型号；未匹配具体手册前联系专业人员，不提供拆机指导。",
        steps=[Step(
            id=str(uuid.uuid4()),
            idx=1,
            content="记录设备完整型号和错误码，核对该型号官方说明书；在核验前不要拆机或旋开滤网。",
            citation_manual="Bosch dishwasher SM/SB 9001014024 B",
            citation_section="PDF p.35（故障表；演示，未确认用户型号）",
        )],
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def _mock_microwave() -> Session:
    return Session(
        id=str(uuid.uuid4()),
        device_category="microwave",
        decision="refused",
        decision_reason="微波炉内部高压电容断电后仍可致命，属于高危类目，不提供任何拆解步骤。",
        safety_refused=True,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def _mock_named(category, brand, reason, instructions, tools="无需工具", citation="演示用合成内容（未核验官方手册）", sections=None):
    return Session(
        id=str(uuid.uuid4()),
        device_category=category,
        brand=brand,
        decision="diy",
        decision_reason=reason + " 工具：" + tools,
        steps=[
            Step(
                id=str(uuid.uuid4()),
                idx=i,
                content=text,
                citation_manual=citation,
                citation_section=sections[i - 1] if sections else f"mock step {i}",
            )
            for i, text in enumerate(instructions, 1)
        ],
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def _mock_router():
    return _mock_named(
        "router",
        "TP-Link",
        "红灯可能表示上游连接异常；此为演示数据。",
        [
            "检查外置电源与网线是否插牢，不拆机。",
            "按设备用户指南重启，等待启动完成；不要恢复出厂设置。",
            "如仍无法联网，记录指示灯状态并联系网络运营商。",
        ],
        citation="TP-Link TL-WR940N REV6.0.2（演示型号）",
        sections=["PDF p.11–12", "PDF p.121", "PDF p.120–122"],
    )


def _mock_billy():
    return _mock_named(
        "furniture",
        "IKEA",
        "BILLY 组装检查演示，须以实际型号说明书为准。",
        [
            "先确认实际型号，阅读并遵循该型号说明书的每一步要求。",
            "使用说明书要求的防倾倒连接件；墙体固定螺钉和膨胀件须适配墙体。",
            "无法确定墙体材料或固定方法时，请寻求专业人员建议。",
        ],
        "适配墙体的螺钉和膨胀件；其他工具以实际型号说明书为准",
        citation="IKEA BILLY AA-2289105-4",
        sections=["PDF p.2", "PDF p.2", "PDF p.2"],
    )


@app.get("/api/health")
def health():
    return {"status": "ok", "mock": MOCK_MODE, "provider": "mock"}


@app.post("/api/manuals/search")
def search_manuals_endpoint(req: ManualSearchRequest):
    if not req.query.strip():
        raise HTTPException(status_code=422, detail="query must not be blank")
    try:
        matches = search_manuals(
            DB.path,
            req.query,
            category=req.category,
            category_hint=req.category_hint,
            brand=req.brand,
            error_code=req.error_code,
            manual_id=req.manual_id,
            limit=req.limit,
        )
    except (sqlite3.Error, OSError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Manual database unavailable; check corpus import.",
        ) from exc
    return {
        "matched": bool(matches),
        "matches": matches,
        "message": "找到候选片段，请核对型号。" if matches else "未找到匹配说明书，当前无可用引用。",
    }


@app.post("/api/analyze/image", response_model=Session)
async def analyze_image(file: UploadFile):
    name = (file.filename or "").lower()
    data = await file.read(MAX_BYTES + 1)
    await file.close()
    quality = check_image(data)
    if not quality.accepted:
        raise HTTPException(status_code=422, detail=quality.reason)
    if "router" in name or "tp-link" in name:
        session = _mock_router()
    elif "billy" in name or "ikea" in name:
        session = _mock_billy()
    elif "report" in name:
        session = _mock_e24()
        session.decision = "landlord"
        session.decision_reason = "演示报修：租住房屋设备问题，请联系房东安排处理。"
    elif "microwave" in name:
        session = _mock_microwave()
    elif "e24" in name:
        session = _mock_e24()
    else:
        raise HTTPException(
            status_code=422,
            detail="未匹配演示场景，请使用文档约定的 mock 文件名；当前未启用真实识别。",
        )
    session = _apply_safety(session)
    DB[session.id] = session
    return session


@app.post("/api/diagnose/manual", response_model=Session)
def diagnose_manual(req: ManualDiagnoseRequest):
    if not req.brand.strip() or not req.error_code.strip():
        raise HTTPException(status_code=422, detail="brand and error_code must not be blank")
    try:
        data = diagnose_manual_data(DB.path, req.brand, req.error_code)
    except (sqlite3.Error, OSError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Manual database unavailable; check corpus import.",
        ) from exc
    session = Session.model_validate(data)
    DB[session.id] = session
    return session


@app.get("/api/sessions", response_model=list[Session])
def list_sessions():
    return sorted(DB.values(), key=lambda session: session.created_at, reverse=True)


@app.get("/api/sessions/{session_id}", response_model=Session)
def get_session(session_id: str):
    if session_id not in DB:
        raise HTTPException(status_code=404, detail="session not found")
    return DB[session_id]


@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: str):
    if session_id not in DB:
        raise HTTPException(status_code=404, detail="session not found")
    del DB[session_id]
    return {"deleted": True}


@app.post("/api/sessions/{session_id}/steps/{step_id}/feedback", response_model=Session)
def step_feedback(session_id: str, step_id: str, req: FeedbackRequest):
    get_session(session_id)
    if not DB.set_feedback(session_id, step_id, req.feedback):
        raise HTTPException(status_code=404, detail="step not found")
    return get_session(session_id)


@app.post("/api/sessions/{session_id}/report")
def generate_report(session_id: str, req: ReportRequest):
    session = get_session(session_id)
    try:
        content = build_report(session, req.lang, req.photo_refs)
    except TranslationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    DB.save_report(session_id, req.lang, content)
    return {"lang": req.lang, "content": content}


from ui_api import install_ui_api

install_ui_api(app, lambda: DB, lambda: bool(globals().get("MOCK_MODE", True)))
