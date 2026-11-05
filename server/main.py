"""SnapFix FastAPI 后端骨架。

当前为 mock 确定性模式:不设 API key 即可跑通 PRD 第 10 节的全部 v1 契约,
供前端并行开发与课堂演示兜底。真实管线(vision/RAG/安全门)按 PRD 第 8 节
在 pipeline.py 中逐步实现,接口保持不变。
"""
import os
import uuid
from datetime import datetime, timezone

from pathlib import Path
from session_store import SessionStore

from fastapi import FastAPI, HTTPException, UploadFile
import sqlite3
from typing import Annotated, Literal

from pydantic import BaseModel, Field
from diagnosis_service import diagnose_manual_data
from report_service import build_report
from retrieval_service import search_manuals
from translation_service import TranslationError
app = FastAPI(title="SnapFix API", version="0.1.0")

MOCK_MODE = True  # 当前没有接通真实模型 provider。

# ---------- 数据模型(对齐 PRD 第 9 节,先内存实现,BE-2 负责落 SQLite) ----------

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
    decision: str  # diy / landlord / professional / refused
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

# ---------- mock 场景(验收场景 2 与 4,D 线后续扩充为 6 个) ----------

def _mock_e24() -> Session:
    return Session(
        id=str(uuid.uuid4()), device_category="dishwasher",
        brand="Bosch", model=None, error_code="E24", decision="professional",
        decision_reason="离线演示数据：请核对完整型号，不提供未经核实的维修步骤。",
        steps=[Step(
            id=str(uuid.uuid4()), idx=1,
            content="记录设备完整型号和错误码，联系品牌售后核对适用说明书。",
            citation_manual="mock 演示内容（未核验实际型号）",
            citation_section="无已核实引用",
        )],
        created_at=datetime.now(timezone.utc).isoformat(),
    )

def _mock_microwave() -> Session:
    return Session(
        id=str(uuid.uuid4()),
        device_category="microwave",
        decision="refused",
        decision_reason="微波炉内部高压电容断电后仍可致命,属于高危类目,不提供任何拆解步骤。",
        safety_refused=True,
        created_at=datetime.now(timezone.utc).isoformat(),
    )

# ---------- API v1 契约(PRD 第 10 节) ----------

@app.get("/api/health")
def health():
    return {"status": "ok", "mock": MOCK_MODE,
            "provider": "mock" if MOCK_MODE else "gemini"}

@app.post("/api/manuals/search")
def search_manuals_endpoint(req: ManualSearchRequest):
    if not req.query.strip():
        raise HTTPException(status_code=422, detail="query must not be blank")
    try:
        matches = search_manuals(
            DB.path, req.query, category=req.category,
            category_hint=req.category_hint,
            brand=req.brand,
            error_code=req.error_code, manual_id=req.manual_id, limit=req.limit,
        )
    except (sqlite3.Error, OSError):
        raise HTTPException(status_code=503, detail="Manual database unavailable; check corpus import.")
    return {
        "matched": bool(matches), "matches": matches,
        "message": "找到候选片段，请核对型号。" if matches else "未找到匹配说明书，当前无可用引用。",
    }

@app.post("/api/analyze/image", response_model=Session)
async def analyze_image(file: UploadFile):
    # mock:按文件名关键词路由到场景;真实管线:质量门→vision→检索→安全门→生成
    name = (file.filename or "").lower()
    await file.read()  # 隐私:照片处理后即删,不持久化
    if "microwave" in name:
        session = _mock_microwave()
    else:
        session = _mock_e24()
    DB[session.id] = session
    return session

@app.post("/api/diagnose/manual", response_model=Session)
def diagnose_manual(req: ManualDiagnoseRequest):
    if not req.brand.strip() or not req.error_code.strip():
        raise HTTPException(status_code=422, detail="brand and error_code must not be blank")
    try:
        data = diagnose_manual_data(DB.path, req.brand, req.error_code)
    except (sqlite3.Error, OSError):
        raise HTTPException(status_code=503, detail="Manual database unavailable; check corpus import.")
    session = Session.model_validate(data)
    DB[session.id] = session
    return session

@app.get("/api/sessions", response_model=list[Session])
def list_sessions():
    return sorted(DB.values(), key=lambda s: s.created_at, reverse=True)

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
def step_feedback(
    session_id: str,
    step_id: str,
    req: FeedbackRequest,
):
    get_session(session_id)
    updated = DB.set_feedback(
        session_id,
        step_id,
        req.feedback,
    )
    if not updated:
        raise HTTPException(
            status_code=404,
            detail="step not found",
        )
    return get_session(session_id)

@app.post("/api/sessions/{session_id}/report")
def generate_report(session_id: str, req: ReportRequest):
    session = get_session(session_id)

    try:
        content = build_report(session, req.lang, req.photo_refs)
    except TranslationError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    DB.save_report(session_id, req.lang, content)

    return {
        "lang": req.lang,
        "content": content,
    }