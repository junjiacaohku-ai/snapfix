"""SnapFix FastAPI 后端骨架。

当前为 mock 确定性模式:不设 API key 即可运行六场景接口演示,
供前端并行开发与课堂演示兜底。真实管线(vision/RAG/安全门)按 PRD 第 8 节
在 pipeline.py 中逐步实现,接口保持不变。
"""
import re
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, UploadFile
from pydantic import BaseModel

app = FastAPI(title="SnapFix API", version="0.1.0")

MOCK_MODE = True  # This branch has no live provider; keys must not change reported status.

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

DB: dict[str, Session] = {}

# ---------- 六场景 mock 数据；文件名路由不代表真实图像识别 ----------

def _mock_e24() -> Session:
    return Session(
        id=str(uuid.uuid4()),
        device_category="dishwasher",
        brand="Bosch", model=None, error_code="E24",
        decision="professional",
        decision_reason="Bosch E24 演示：洗碗机排水异常。请先核对完整型号；未匹配具体手册前联系专业人员，不提供拆机指导。",
        steps=[Step(id=str(uuid.uuid4()), idx=1,
                    content="记录设备完整型号和错误码，核对该型号官方说明书；在核验前不要拆机或旋开滤网。",
                    citation_manual="Bosch dishwasher SM/SB 9001014024 B",
                    citation_section="PDF p.35（故障表；演示，未确认用户型号）")],
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

def _mock_named(category, brand, reason, instructions, tools="无需工具", citation="演示用合成内容（未核验官方手册）", sections=None):
    return Session(
        id=str(uuid.uuid4()), device_category=category, brand=brand,
        decision="diy", decision_reason=reason + " 工具：" + tools,
        steps=[Step(id=str(uuid.uuid4()), idx=i, content=text,
                    citation_manual=citation,
                    citation_section=sections[i-1] if sections else f"mock step {i}")
               for i, text in enumerate(instructions, 1)],
        created_at=datetime.now(timezone.utc).isoformat())


def _mock_router():
    return _mock_named("router", "TP-Link", "红灯可能表示上游连接异常；此为演示数据。", [
        "检查外置电源与网线是否插牢，不拆机。",
        "按设备用户指南重启，等待启动完成；不要恢复出厂设置。",
        "如仍无法联网，记录指示灯状态并联系网络运营商。"],
        citation="TP-Link TL-WR940N REV6.0.2（演示型号）",
        sections=["PDF p.11–12", "PDF p.121", "PDF p.120–122"])


def _mock_billy():
    return _mock_named("furniture", "IKEA", "BILLY 组装检查演示，须以实际型号说明书为准。", [
        "先确认实际型号，阅读并遵循该型号说明书的每一步要求。",
        "使用说明书要求的防倾倒连接件；墙体固定螺钉和膨胀件须适配墙体。",
        "无法确定墙体材料或固定方法时，请寻求专业人员建议。"],
        "适配墙体的螺钉和膨胀件；其他工具以实际型号说明书为准",
        citation="IKEA BILLY AA-2289105-4", sections=["PDF p.2", "PDF p.2", "PDF p.2"])


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
    if any(token in name for token in ("blur", "dark", "blurry")):
        raise HTTPException(status_code=422, detail="照片模糊或过暗，请补光、对焦后重拍。")
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
        raise HTTPException(status_code=422, detail="未匹配演示场景，请使用文档约定的 mock 文件名；当前未启用真实识别。")
    DB[session.id] = session
    return session

@app.post("/api/diagnose/manual", response_model=Session)
def diagnose_manual(req: ManualDiagnoseRequest):
    code = re.sub(r'^E\s*[:：]?\s*(\d+)$', r'E\1', req.error_code.strip().upper())
    if req.brand.strip().lower() in {"bosch", "博世"} and code == "E24":
        session = _mock_e24()
    else:
        raise HTTPException(status_code=404, detail="mock 暂无该品牌和错误码，请核对设备型号或联系专业人员。")
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
def step_feedback(session_id: str, step_id: str, req: FeedbackRequest):
    session = get_session(session_id)
    for step in session.steps:
        if step.id == step_id:
            step.feedback = req.feedback
            return session
    raise HTTPException(status_code=404, detail="step not found")

@app.post("/api/sessions/{session_id}/report")
def generate_report(session_id: str, req: ReportRequest):
    s = get_session(session_id)
    if req.lang == "en":
        tried = ", ".join(f"step {st.idx}" for st in s.steps if st.feedback == "done") or "none"
        content = (f"Repair request: {s.device_category}"
                   f"{f' ({s.brand})' if s.brand else ''}"
                   f"{f', error code {s.error_code}' if s.error_code else ''}. "
                   f"Steps already tried: {tried}. Please attach a photo when sending this request. Please advise.")
    else:
        tried = "、".join(f"步骤{st.idx}" for st in s.steps if st.feedback == "done") or "无"
        content = (f"报修申请:{s.device_category}"
                   f"{f'({s.brand})' if s.brand else ''}"
                   f"{f',错误码 {s.error_code}' if s.error_code else ''}。"
                   f"已尝试步骤:{tried}。发送时请另附照片,烦请安排处理,谢谢。")
    return {"lang": req.lang, "content": content}
