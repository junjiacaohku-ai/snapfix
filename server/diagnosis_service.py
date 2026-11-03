from datetime import datetime, timezone
import re
import uuid

from retrieval import normalize_brand
from retrieval_service import search_manuals
from safety_gate import check


def normalize_code(value: str) -> str:
    return re.sub(r"^E\s*[:：]?\s*(\d+)$", r"E\1", value.strip().upper())


def diagnose_manual_data(database, brand: str, error_code: str):
    code = normalize_code(error_code)
    canonical_brand = normalize_brand(brand)
    data = dict(
        id=str(uuid.uuid4()), device_category="unknown",
        brand=canonical_brand or None, model=None, error_code=code or None,
        decision="professional", decision_reason="", steps=[],
        safety_refused=False, created_at=datetime.now(timezone.utc).isoformat(),
    )
    verdict = check(brand, error_code)
    if verdict.refused:
        data.update(decision="refused", safety_refused=True,
                    decision_reason=verdict.reason + " " + verdict.advice)
        return data
    matches = search_manuals(
        database, f"{canonical_brand} {code}",
        brand=canonical_brand, error_code=code, limit=3,
    )
    if not matches:
        data["decision_reason"] = (
            "未找到匹配说明书，当前无可用引用。请核对设备类别、完整型号和错误码，"
            "或联系品牌售后；不提供未经核实的维修步骤。"
        )
        return data
    categories = {row["device_category"] for row in matches}
    if len(categories) == 1:
        data["device_category"] = categories.pop()
    verdict = check(data["device_category"], brand, error_code)
    if verdict.refused:
        data.update(decision="refused", safety_refused=True,
                    decision_reason=verdict.reason + " " + verdict.advice)
        return data
    top = matches[0]
    data["decision_reason"] = (
        f"已检索到候选说明书：{top['title']}，PDF 第 {top['page']} 页。"
        "这是候选资料，设备完整型号尚未核实；当前仅完成检索接入，"
        "不生成维修步骤。请核对实际型号，必要时联系专业人员。"
    )
    return data