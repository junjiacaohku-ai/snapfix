"""Live image diagnosis with retrieval, safety and citation validation."""
from datetime import datetime, timezone
import uuid

from diagnosis_service import normalize_code
from providers import gemini_extract, gemini_generate
from retrieval import normalize_category
from retrieval_service import search_manuals
from safety_gate import check as check_safety


def diagnose_image(
    image_bytes: bytes,
    database,
    mime_type="image/jpeg",
    *,
    vision_extract=gemini_extract,
    generate=gemini_generate,
    search=search_manuals,
):
    vision = vision_extract(image_bytes, mime_type)
    if vision is None:
        return None

    category = normalize_category(vision.device_category) or "unknown"
    brand = (vision.brand or "").strip() or None
    model = (vision.model or "").strip() or None
    code = normalize_code(vision.error_code or "") or None
    data = {
        "id": str(uuid.uuid4()),
        "device_category": category,
        "brand": brand,
        "model": model,
        "error_code": code,
        "decision": "professional",
        "decision_reason": "",
        "steps": [],
        "safety_refused": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_mode": "gemini",
    }
    verdict = check_safety(
        category,
        brand,
        model,
        code,
        *vision.visible_faults,
    )
    if verdict.refused:
        data.update(
            decision="refused",
            decision_reason=verdict.reason + " " + verdict.advice,
            safety_refused=True,
        )
        return data

    if vision.confidence < 0.55:
        data["decision_reason"] = (
            "图片识别置信度较低，无法可靠确认设备或故障。请重新拍摄铭牌和错误码，"
            "或改用手动输入；不提供猜测性维修步骤。"
        )
        return data

    query = " ".join(
        value
        for value in [category, brand, model, code, *vision.visible_faults]
        if value
    )
    matches = search(
        database,
        query,
        category=category if category != "unknown" else "",
        category_hint=category,
        brand=brand or "",
        error_code=code or "",
        limit=3,
    )
    if not matches:
        data["decision_reason"] = (
            "未找到与当前设备和故障匹配的手册片段，当前无可用引用。"
            "请核对完整型号或联系品牌售后，不提供未经核实的维修步骤。"
        )
        return data

    generated = generate(vision, matches)
    if generated is None:
        return None

    by_id = {row["id"]: row for row in matches}
    steps = []
    for item in generated.steps:
        source = by_id.get(item.citation_chunk_id)
        content = item.content.strip()
        if source is None or not content:
            continue
        if check_safety(category, brand, content).refused:
            continue
        steps.append({
            "id": str(uuid.uuid4()),
            "idx": len(steps) + 1,
            "content": content,
            "citation_manual": source["title"],
            "citation_section": f"PDF p.{source['page']} · {source['id']}",
            "feedback": None,
        })

    decision = generated.decision if generated.decision in {"diy", "landlord", "professional"} else "professional"
    if decision == "diy" and not model:
        decision = "professional"
        data["decision_reason"] = (
            "设备完整型号尚未核实，不能确认生成步骤是否适用。请核对型号或联系品牌售后。"
        )
        return data
    if decision == "diy" and not steps:
        data["decision_reason"] = (
            "生成内容未通过手册引用或安全校验，已丢弃自行维修步骤。请核对型号或联系专业人员。"
        )
        return data

    data["decision"] = decision
    data["decision_reason"] = generated.decision_reason.strip() or "已根据图片和检索手册生成处置建议。"
    if decision == "diy":
        data["steps"] = steps
    return data
