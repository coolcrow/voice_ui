"""赛博朋克风格消息文案"""

TX_OK = "[VOICE::TX] 信号已发出 → {text}"
TX_NULL = "[VOICE::NULL] 空载波，传输终止"
TX_ERR = "[VOICE::ERR] 传输中断"
TX_TIMEOUT = "[VOICE::TIMEOUT] 信号衰减"
SCAN_HEADER = "[VOICE::SCAN] 频段扫描结果"
BOOT_TITLE = "[VOICE::SYS] ═══ 语音矩阵已上线 ═══"
BOOT_STATUS = "[VOICE::SYS] 信号锁定 · 频段正常 · 等待指令"


def format_result(raw: str) -> str:
    """将引擎原始返回映射为赛博朋克风格文案。"""
    if not raw:
        return TX_NULL

    if "为空" in raw or "跳过" in raw:
        return TX_NULL
    if raw == "朗读失败":
        return TX_ERR
    if "超时" in raw:
        return TX_TIMEOUT
    if "已朗读" in raw:
        snippet = raw.replace("已朗读: ", "").replace("已朗读:", "")
        if len(snippet) > 60:
            snippet = snippet[:60] + "..."
        return TX_OK.format(text=snippet)
    if "无可用" in raw:
        return "[VOICE::ERR] 频段扫描失败"
    if "可用语音" in raw or "voice" in raw.lower():
        return raw.replace("edge-tts 可用语音", SCAN_HEADER).replace("可用语音", SCAN_HEADER)

    return raw