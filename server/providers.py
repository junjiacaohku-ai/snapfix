"""Provider 适配层(PRD §8):Gemini 主用 → OpenAI 兼容兜底 → mock 降级。

约定:任何函数拿不到 key 或调用失败都返回 None,由上层管线降级到
mock 确定性模式——mock 永远可用,是演示兜底的生命线。
key 只从环境变量/.env 读取,绝不出现在代码与日志里。
"""
from __future__ import annotations

import json
import os

from pydantic import BaseModel

try:  # 有 python-dotenv 就自动加载 server/.env,没有也能靠真实环境变量跑
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


class VisionResult(BaseModel):
    """Vision 提取的结构化输出(PRD §8 第②步)。"""
    device_category: str
    brand: str | None = None
    model: str | None = None
    error_code: str | None = None
    visible_faults: list[str] = []
    confidence: float = 0.0


_VISION_PROMPT = """你是家电维修诊断系统的视觉提取模块。观察这张照片,只输出 JSON,字段:
device_category(设备类别,英文 snake_case,如 washing_machine/router/microwave/ikea_furniture)
brand(品牌,认不出为 null)
model(型号,认不出为 null)
error_code(屏幕上/铭牌上的错误码,没有为 null)
visible_faults(可见故障迹象,中文短语列表)
confidence(0-1 之间,整体识别置信度)
拿不准就把 confidence 调低,不要编造型号。"""

_GEMINI_MODEL = "gemini-2.5-flash"


def gemini_extract(image_bytes: bytes, mime_type: str = "image/jpeg") -> VisionResult | None:
    """Gemini 多模态提取。无 key 或任何失败都返回 None(上层降级)。"""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return None
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=key)
        resp = client.models.generate_content(
            model=_GEMINI_MODEL,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                _VISION_PROMPT,
            ],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        return VisionResult.model_validate(json.loads(resp.text))
    except Exception:
        return None


class GeneratedStep(BaseModel):
    content: str
    citation_chunk_id: str


class GeneratedDiagnosis(BaseModel):
    decision: str
    decision_reason: str
    steps: list[GeneratedStep] = []


def gemini_generate(vision: VisionResult, matches: list[dict]) -> GeneratedDiagnosis | None:
    """Generate a decision and steps constrained to retrieved manual chunks."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key or not matches:
        return None
    manuals = [
        {
            "chunk_id": row["id"],
            "title": row["title"],
            "manual_id": row["manual_id"],
            "page": row["page"],
            "section": row.get("section") or row.get("chapter") or "",
            "content": row["content"],
        }
        for row in matches
    ]
    prompt = (
        "你是家电故障处置助手。只能依据给定手册片段生成答案，不得补充常识性拆修步骤。"
        "输出 decision=diy/landlord/professional、一句话 decision_reason 和 steps。"
        "每个 step 必须包含 content 和来自输入的 citation_chunk_id。"
        "如果设备完整 model 为 null、手册型号不匹配、资料不足或需要拆机，decision 必须为 professional，steps 为空。"
        "燃气、市电、高压电容、制冷剂、锂电池、压力设备等高危作业不得给出 DIY。"
        "租住房屋且非用户所有的设备可建议 landlord。不要声称已执行任何操作。\n\n"
        "视觉提取："
        + json.dumps(vision.model_dump(), ensure_ascii=False)
        + "\n手册片段："
        + json.dumps(manuals, ensure_ascii=False)
    )
    try:
        from google import genai
        from google.genai import types

        with genai.Client(
            api_key=key,
            http_options=types.HttpOptions(timeout=25000),
        ) as client:
            resp = client.models.generate_content(
                model=os.environ.get("GEMINI_MODEL", _GEMINI_MODEL),
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=GeneratedDiagnosis,
                ),
            )
        return GeneratedDiagnosis.model_validate(json.loads(resp.text))
    except Exception:
        return None


def status() -> dict:
    """供 /api/health 汇报 provider 配置状态(只报有无,绝不报 key 本体)。"""
    return {
        "gemini": bool(os.environ.get("GEMINI_API_KEY")),
        "openai_compatible": bool(os.environ.get("OPENAI_API_KEY")),
    }
