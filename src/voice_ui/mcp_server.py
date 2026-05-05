#!/usr/bin/env python3
"""Voice TTS MCP Server

赛博朋克风格语音输出 — 信号锁定 · 频段正常 · 等待指令。

配置（在 .claude/settings.json 中添加）:
{
  "mcpServers": {
    "voice-tts": {
      "command": "/path/to/voice_ui/.venv/bin/python",
      "args": ["-m", "voice_ui.mcp_server"]
    }
  }
}
"""

import os
import sys

from mcp.server.fastmcp import FastMCP

from .style import BOOT_STATUS, BOOT_TITLE, format_result
from .synth import SynthEngine
from .tts import TTSProvider

MCP_MARK_FILE = "/tmp/.voice_ui_mcp_spoken"

mcp = FastMCP("voice-tts")

_provider: TTSProvider | None = None
_synth: SynthEngine | None = None
_config: dict = {}


def _get_provider() -> TTSProvider:
    global _provider
    if _provider is None:
        from .config import load_config

        _config.update(load_config())
        _provider = TTSProvider(_config)
    return _provider


def _get_synth() -> SynthEngine:
    global _synth
    if _synth is None:
        if not _config:
            from .config import load_config

            _config.update(load_config())
        _synth = SynthEngine(_config)
    return _synth


def _boot() -> None:
    """赛博朋克启动仪式。"""
    print(f"\n{BOOT_TITLE}", file=sys.stderr)
    print(BOOT_STATUS, file=sys.stderr)
    _get_synth().play("boot")


def _touch_mark() -> None:
    """写入标记文件，告诉 Hook 本次已通过 MCP 播报。"""
    try:
        with open(MCP_MARK_FILE, "w") as f:
            f.write("")
    except OSError:
        pass


@mcp.tool()
def speak(text: str, voice: str = "", rate: int = 180) -> str:
    """朗读文本内容。当你想用语音通知用户重要信息时调用此工具。

    Args:
        text: 要朗读的文本内容
        voice: 语音名称（各引擎有不同的语音列表，可用 list_voices 查看）
        rate: 语速（每分钟词数，默认 180）

    使用规则：
    - 文本控制在 100 字以内，避免超时
    - 不要朗读代码，只说自然语言摘要
    """
    synth = _get_synth()
    synth.play("pre_speak")
    raw = _get_provider().speak_sync(text, voice=voice, rate=rate)
    synth.play("post_speak")
    _touch_mark()
    return format_result(raw)


@mcp.tool()
def notify(text: str, event: str = "") -> str:
    """发送简短语音通知。适合读一句话的摘要，如任务完成、发现错误等。

    Args:
        text: 通知内容（建议 50 字以内）
        event: 事件类型 "success" / "error" / "warning" / "waiting"，不传用默认音效

    必须调用的场景：
    1. 任务完成时 — event="" 或 "success"
    2. 发现错误/警告时 — event="error" 或 "warning"
    3. 等待用户选择/输入时 — event="waiting"（使用等待提示音）
    4. 每轮回复结束时 — event=""，作为最后一步调用

    注意：notify 必须是回复的绝对最后一步，调用后不能再输出任何文字。
    """
    synth = _get_synth()
    if event in ("success", "error", "warning", "waiting"):
        synth.play(event)
    else:
        synth.play("pre_speak")

    raw = _get_provider().speak_sync(text)
    synth.play("post_speak")
    _touch_mark()
    return format_result(raw)


@mcp.tool()
def list_voices() -> str:
    """列出当前 TTS 引擎可用的语音。"""
    raw = _get_provider().list_voices()
    return format_result(raw)


if __name__ == "__main__":
    _boot()
    mcp.run()
