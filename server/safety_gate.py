"""安全门:生成前的规则拦截层(PRD F3,不可砍)。

规则分类器先于任何 LLM 生成执行;命中高危类目即短路拒答,
只返回拒答说明 + 风险解释 + 专业求助建议。纯规则、零依赖、确定性输出。
验收标准(PRD §12):高危测试集 100% 拒答,正常类目不误伤。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SafetyVerdict:
    refused: bool
    category: str | None = None
    reason: str = ""
    advice: str = ""


# (类目, 触发关键词(中英,小写匹配), 风险解释, 求助建议)
_RULES: list[tuple[str, list[str], str, str]] = [
    (
        "微波炉高压电容",
        ["微波炉", "microwave", "高压电容", "capacitor", "磁控管", "magnetron"],
        "微波炉内部高压电容断电后仍可储存致命电量,自行拆解有触电致死风险。",
        "停止使用,联系品牌售后或持牌维修师傅。",
    ),
    (
        "燃气设备",
        ["燃气", "煤气", "天然气", "gas", "gas heater", "燃气热水器", "煤气灶", "gas stove"],
        "燃气泄漏可致爆炸或一氧化碳中毒,任何拆装都可能破坏密封。",
        "关闭燃气总阀、开窗通风、不要触碰电器开关,联系持牌燃气技工。",
    ),
    (
        "制冷剂回路",
        ["冷媒", "雪种", "制冷剂", "refrigerant", "freon", "加氟", "空调不冷"],
        "制冷剂回路为高压封闭系统,拆接需持牌资质,泄漏危害人身与环境。",
        "联系持牌空调维修商;可加氟之外的外观清洁可自行处理。",
    ),
    (
        "锂电池拆解",
        ["电池拆解", "电芯", "18650", "lithium", "battery pack", "拆电池", "鼓包电池", "鼓包"],
        "锂电池刺穿或短路会起火爆炸,鼓包电池尤其危险。",
        "不要穿刺或拆解;鼓包电池放入防火容器,送电子产品回收点。",
    ),
    (
        "市电配电",
        ["配电箱", "电闸", "breaker", "mains", "强电", "漏电开关", "总闸", "改电路", "接线"],
        "220V 市电作业可致命,非持牌电工操作亦属违规。",
        "断开总闸仅作应急,任何接线改动请联系持牌电工。",
    ),
    (
        "电热水器内部",
        ["电热水器", "加热管", "加热棒", "heating element", "water heater element"],
        "电热水器内部同时涉及市电与水路,拆装失误可致漏电或漏水。",
        "联系持牌电工或品牌售后;外部复位键/泄压阀操作可参考手册自行尝试。",
    ),
    (
        "高空/外机作业",
        ["空调外机", "窗外", "高空", "窗台外", "outdoor unit", "外墙"],
        "高空作业坠落风险极高,香港法例对室外悬空作业有安全要求。",
        "任何需要探身窗外的作业都交给有保险的专业人员。",
    ),
    (
        "电焊/切割",
        ["电焊", "welding", "切割", "angle grinder", "角磨机"],
        "电焊与切割产生高温火花与强光,需专业防护与资质。",
        "联系持证技工;不要在不通风的室内操作。",
    ),
    (
        "化学品混用",
        ["漂白水", "bleach", "氨水", "ammonia", "通渠水", "drain cleaner", "混合清洁剂"],
        "漂白水与酸性/氨类清洁剂混合会产生有毒气体。",
        "立即通风并撤离;永远不要混合使用清洁剂。",
    ),
    (
        "石棉/老旧建材",
        ["石棉", "asbestos"],
        "石棉纤维吸入致癌,香港旧楼部分建材可能含石棉。",
        "不要打磨或钻孔,联系屋宇署认可的石棉顾问。",
    ),
    (
        "承重结构",
        ["承重墙", "承重柱", "load-bearing", "拆墙", "打墙"],
        "改动承重结构影响全楼安全,且须屋宇署批准。",
        "任何墙体改动前先咨询大厦管理处与注册结构工程师。",
    ),
    (
        "电梯",
        ["电梯", "lift", "elevator", "扶梯"],
        "电梯系统由注册承办商专营,非授权操作极其危险且违法。",
        "联系大厦管理处或电梯保养承办商。",
    ),
]


def check(*texts: str | None) -> SafetyVerdict:
    """对任意组合的文本(设备类别/品牌/故障描述/错误码)做高危匹配。

    管线在拿到归一化结果后、生成步骤前调用;refused=True 时直接短路拒答。
    """
    haystack = " ".join(t for t in texts if t).lower()
    for category, keywords, reason, advice in _RULES:
        if any(kw.lower() in haystack for kw in keywords):
            return SafetyVerdict(refused=True, category=category, reason=reason, advice=advice)
    return SafetyVerdict(refused=False)


if __name__ == "__main__":
    # 自检冒烟:高危应全部拒答,正常应全部放行(张帆的完整测试集到位后替换)
    dangerous = [
        "微波炉不加热", "microwave not heating", "燃气热水器打不着火",
        "空调不冷要加雪种", "电池鼓包想拆开看", "配电箱跳闸烧焦味",
        "想拆承重墙", "漂白水混合通渠水",
    ]
    safe = [
        "洗衣机报 E24", "washing machine not draining", "路由器红灯",
        "IKEA BILLY 书架组装", "IKEA 书桌少螺丝", "水龙头滴水换阀芯",
    ]
    failures = []
    for t in dangerous:
        v = check(t)
        if not v.refused:
            failures.append(f"漏拦: {t}")
    for t in safe:
        v = check(t)
        if v.refused:
            failures.append(f"误伤: {t} -> {v.category}")
    for t in dangerous:
        v = check(t)
        print(f"{'拒答' if v.refused else '放行'}  [{v.category or '-'}]  {t}")
    for t in safe:
        v = check(t)
        print(f"{'拒答' if v.refused else '放行'}  [{v.category or '-'}]  {t}")
    if failures:
        raise SystemExit("自检失败: " + "; ".join(failures))
    print("\n自检通过:高危全拦,正常全过")
