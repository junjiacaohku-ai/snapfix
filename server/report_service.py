from translation_service import TranslationError, translate_texts


CATEGORY_ZH = {
    "dishwasher": "洗碗机",
    "washing_machine": "洗衣机",
    "router": "路由器",
    "microwave": "微波炉",
    "furniture": "家具",
    "ikea_furniture": "宜家家具",
    "unknown": "未知",
}


def build_report(session, lang: str, photo_refs=()) -> str:
    if lang not in {"zh", "en"}:
        raise ValueError("Unsupported report language")

    completed = [
        step
        for step in sorted(session.steps, key=lambda step: step.idx)
        if step.feedback == "done"
    ]
    photos = "; ".join(photo_refs)

    if lang == "en":
        # 保留旧版能力：无密钥时也能生成英文报告。
        category = session.device_category.replace("_", " ")
        tried = "\n".join(
            f"- Step {step.idx} (marked complete)."
            for step in completed
        )
        note = ""

        # 翻译只是增强功能，失败不能阻止报告生成。
        if completed:
            try:
                translated = translate_texts(
                    [
                        session.device_category,
                        *[step.content for step in completed],
                    ],
                    "en",
                )
                category = translated[0]
                tried = "\n".join(
                    f"- {text}"
                    for text in translated[1:]
                )
            except TranslationError:
                note = (
                    "Step descriptions were not translated. "
                    "Completed step numbers are listed above; "
                    "please refer to the original diagnosis for details.\n"
                )

        return (
            "Repair request\n"
            f"Device: {category}\n"
            f"Brand: {session.brand or 'Unknown'}\n"
            f"Model: {session.model or 'Unknown'}\n"
            f"Error code: {session.error_code or 'Not provided'}\n"
            "Steps already tried:\n"
            f"{tried or '- No completed steps recorded.'}\n"
            f"{note}"
            f"Photo references: {photos or 'Not provided'}\n"
            "Please attach a photo or photos when sending this request.\n"
            "Please advise or arrange an inspection."
        )

    # 中文沿用诊断原文，不需要 Gemini。
    category = CATEGORY_ZH.get(
        session.device_category,
        session.device_category,
    )
    tried = "\n".join(
        f"- 步骤{step.idx}：{step.content}"
        for step in completed
    )

    return (
        "报修申请\n"
        f"设备类别：{category}\n"
        f"品牌：{session.brand or '未知'}\n"
        f"型号：{session.model or '未知'}\n"
        f"错误码：{session.error_code or '未提供'}\n"
        "已尝试步骤：\n"
        f"{tried or '- 暂无已完成步骤。'}\n"
        f"照片引用：{photos or '未提供'}\n"
        "发送时请另附实际照片，烦请提供建议或安排检查，谢谢。"
    )
