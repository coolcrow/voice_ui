#!/usr/bin/env python3
"""Claude Code Hooks 语音方案

Stop 事件触发时，接收 last_assistant_message JSON，
过滤代码块和 noise 后调用 TTS 朗读。

用法（在 .claude/settings.json 中配置）:
{
  "hooks": {
    "Stop": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "python3 -m voice_ui.hook_handler"
      }]
    }]
  }
}
"""

import json
import os
import re
import sys
import time
from typing import Dict

from .tts import TTSProvider

MARK_FILE = "/tmp/.voice_ui_mcp_spoken"
SKIP_WINDOW = 3  # seconds

_provider: TTSProvider | None = None


def _get_provider() -> TTSProvider:
    global _provider
    if _provider is None:
        from .config import load_config

        _provider = TTSProvider(load_config())
    return _provider


def filter_assistant_message(text: str) -> str:
    """从 assistant message 中提取值得朗读的内容"""
    if not text:
        return ""

    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`[^`]+`", "", text)
    text = re.sub(r"#{1,6}\s+", "", text)
    text = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", text)
    text = re.sub(r"/[\w/.<>\-]+", "", text)
    text = re.sub(r"^\|[-| :]+\|$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\|", " ", text)
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^---+$", "", text, flags=re.MULTILINE)

    sentences = re.split(r"(?<=[。！？.!?\n])\s*", text)
    readable = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]

    result = "。".join(readable[:3])

    if len(result) > 300:
        result = result[:300] + "等"

    return result.strip()


def speak_text(text: str, voice: str = "", rate: int = 180) -> None:
    """使用 TTSProvider 朗读（异步非阻塞）。"""
    if not text or len(text) < 5:
        return
    _get_provider().speak(text)


def should_skip() -> bool:
    """检查 MCP 是否刚刚播报过，避免重复。"""
    try:
        if not os.path.exists(MARK_FILE):
            return False
        mtime = os.path.getmtime(MARK_FILE)
        return (time.time() - mtime) < SKIP_WINDOW
    except (OSError, ValueError):
        return False


def main() -> None:
    try:
        raw = sys.stdin.read()
    except Exception:
        return

    if not raw:
        return

    try:
        data: Dict = json.loads(raw)
    except json.JSONDecodeError:
        return

    message = data.get("last_assistant_message", "")
    if not message:
        return

    if should_skip():
        return

    readable = filter_assistant_message(message)
    if readable:
        speak_text(readable)


if __name__ == "__main__":
    main()
