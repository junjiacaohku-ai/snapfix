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
from pydantic import BaseModel

app = FastAPI(title="SnapFix API", version="0.1.0")

MOCK_MODE = not os.environ.get("GEMINI_API_KEY")

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
    feedback: str  # done / not_useful / skipped

class ReportRequest(BaseModel):
    lang: str = "zh"  # zh / en

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
        id=str(uuid.uuid4()),
        device_category="washing_machine",
        brand="Bosch", model=None, error_code="E24",
        decision="diy",
        decision_reason="排水泵滤网堵塞,非破坏性操作,工具只需一枚硬币,约 15 分钟。",
        steps=[
            Step(id=str(uuid.uuid4()), idx=1,
                 content="断电并关闭水龙头,在机器右下角找到排水泵检修口。",
                 citation_manual="Bosch 洗衣机用户手册", citation_section="§7.2"),
            Step(id=str(uuid.uuid4()), idx=2,
                 content="用硬币逆时针旋开滤网盖,垫毛巾接住残水。",
                 citation_manual="Bosch 洗衣机用户手册", citation_section="§7.3"),
            Step(id=str(uuid.uuid4()), idx=3,
                 content="取出滤网清除异物,装回后通电试运行脱水程序。",
                 citation_manual="Bosch 洗衣机用户手册", citation_section="§7.4"),
        ],
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
    code = req.error_code.strip().upper()
    if req.brand.lower() in {"bosch", "博世"} and code == "E24":
        session = _mock_e24()
    else:
        session = _mock_e24()  # mock 兜底,真实管线走检索
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
    s = get_session(session_id)
    if req.lang == "en":
        tried = ", ".join(f"step {st.idx}" for st in s.steps if st.feedback == "done") or "none"
        content = (f"Repair request: {s.device_category}"
                   f"{f' ({s.brand})' if s.brand else ''}"
                   f"{f', error code {s.error_code}' if s.error_code else ''}. "
                   f"Steps already tried: {tried}. "
                   f"Please attach a photo when sending this request. Please advise.")
    else:
        tried = "、".join(f"步骤{st.idx}" for st in s.steps if st.feedback == "done") or "无"
        content = (f"报修申请:{s.device_category}"
                   f"{f'({s.brand})' if s.brand else ''}"
                   f"{f',错误码 {s.error_code}' if s.error_code else ''}。"
                   f"已尝试步骤:{tried}。发送时请另附照片,烦请安排处理,谢谢。")
    DB.save_report(session_id, req.lang, content)
    return {"lang": req.lang, "content": content}
