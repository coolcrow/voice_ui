"""edge-tts 引擎 — 微软 Edge 在线 TTS（免费、高质量、中文支持好）"""

import asyncio
import os
import tempfile

from ._base import TTSEngine
from ._playback import play_audio_file
from . import register_engine


@register_engine
class EdgeTTSEngine(TTSEngine):
    """使用 edge-tts 库调用微软 Edge 在线语音服务。"""

    _engine_name = "edge-tts"

    @property
    def name(self) -> str:
        return self._engine_name

    def __init__(self, config: dict) -> None:
        self.config = config
        self.default_voice = config.get(
            "default_voice", "zh-CN-XiaoxiaoNeural"
        )
        self.default_rate = config.get("default_rate", 180)

    def speak_sync(self, text: str, voice: str = "", rate: int = 180) -> str:
        if not text:
            return "文本为空，跳过朗读"

        try:
            import edge_tts
        except ImportError:
            raise ImportError(
                "edge-tts 未安装。请运行: pip install -e '.[edge-tts]'"
            )

        voice = voice or self.default_voice
        rate = rate or self.default_rate

        rate_str = self._calc_rate(rate)
        communicate = edge_tts.Communicate(text, voice, rate=rate_str)

        tmp_path = tempfile.mktemp(suffix=".mp3")
        try:
            self._run_async(communicate.save(tmp_path))
            play_audio_file(tmp_path)
            return self._success_msg(text)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def list_voices(self) -> str:
        try:
            import edge_tts
        except ImportError:
            return "edge-tts 未安装"

        try:
            voices = self._run_async(edge_tts.list_voices())
            zh_voices = [
                v for v in voices if v["Locale"].startswith("zh-")
            ]
            all_voices = zh_voices + [
                v for v in voices if not v["Locale"].startswith("zh-")
            ]
            lines = []
            for v in all_voices[:30]:
                lines.append(
                    f"- {v['ShortName']} ({v['Locale']}) {v['Gender']}"
                )
            total = len(voices)
            shown = min(len(all_voices), 30)
            return (
                f"edge-tts 可用语音 (显示 {shown}/{total}，"
                f"中文优先):\n" + "\n".join(lines)
            )
        except Exception as e:
            return f"获取语音列表失败: {e}"

    @staticmethod
    def _run_async(coro) -> object:
        """安全运行 async 函数，自动处理已有 event loop 的情况。"""
        import threading

        result: list[object] = []
        exc: list[Exception] = []

        def _run() -> None:
            try:
                loop = asyncio.new_event_loop()
                result.append(loop.run_until_complete(coro))
                loop.close()
            except Exception as e:
                exc.append(e)

        try:
            asyncio.get_running_loop()
            # 已有 loop（如 MCP server），在新线程中运行
            t = threading.Thread(target=_run)
            t.start()
            t.join(timeout=30)
        except RuntimeError:
            # 没有 running loop，直接用 asyncio.run
            return asyncio.run(coro)

        if exc:
            raise exc[0]
        return result[0] if result else None

    @staticmethod
    def _calc_rate(rate: int) -> str:
        """将 rate (wpm) 转为 edge-tts 的 rate 字符串。"""
        percent = int((rate / 180 - 1) * 100)
        if percent >= 0:
            return f"+{percent}%"
        return f"{percent}%"

    @staticmethod
    def _success_msg(text: str) -> str:
        snippet = text[:80]
        suffix = "..." if len(text) > 80 else ""
        return f"已朗读: {snippet}{suffix}"
