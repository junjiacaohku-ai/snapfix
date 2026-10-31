from translation_service import translate_texts


def build_report(session, lang: str, photo_refs=()) -> str:
    if lang not in {"zh", "en"}:
        raise ValueError("Unsupported report language")

    completed = [
        step.content
        for step in sorted(session.steps, key=lambda step: step.idx)
        if step.feedback == "done"
    ]

    # 设备类别与已完成步骤一起转换；其他设备标识保持原值。
    translated = translate_texts(
        [session.device_category, *completed],
        lang,
    )
    category = translated[0]
    tried = "\n".join(
        f"- {text}"
        for text in translated[1:]
    )
    photos = "; ".join(photo_refs)

    if lang == "en":
        return (
            "Repair request\n"
            f"Device: {category}\n"
            f"Brand: {session.brand or 'Unknown'}\n"
            f"Model: {session.model or 'Unknown'}\n"
            f"Error code: {session.error_code or 'Not provided'}\n"
            "Steps already tried:\n"
            f"{tried or '- No completed steps recorded.'}\n"
            f"Photo references: {photos or 'Not provided'}\n"
            "Please attach the actual photos when sending this request.\n"
            "Please advise or arrange an inspection."
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