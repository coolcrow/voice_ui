"""pyttsx3 引擎 — 离线跨平台 TTS"""

from ._base import TTSEngine
from . import register_engine


@register_engine
class Pyttsx3Engine(TTSEngine):
    """使用 pyttsx3 库进行离线语音合成。"""

    _engine_name = "pyttsx3"

    @property
    def name(self) -> str:
        return self._engine_name

    def __init__(self, config: dict) -> None:
        self.config = config

    def speak_sync(self, text: str, voice: str = "", rate: int = 180) -> str:
        if not text:
            return "文本为空，跳过朗读"

        try:
            import pyttsx3
        except ImportError:
            raise ImportError(
                "pyttsx3 未安装。请运行: pip install -e '.[pyttsx3]'"
            )

        engine = pyttsx3.init()
        try:
            engine.setProperty("rate", rate)
            if voice:
                engine.setProperty("voice", voice)
            engine.say(text)
            engine.runAndWait()
            return self._success_msg(text)
        finally:
            engine.stop()

    def list_voices(self) -> str:
        try:
            import pyttsx3
        except ImportError:
            return "pyttsx3 未安装"

        try:
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            engine.stop()
            lines = []
            for v in voices[:20]:
                lines.append(f"- {v.name} ({v.languages[0] if v.languages else '?'})")
            return "pyttsx3 可用语音:\n" + "\n".join(lines)
        except Exception as e:
            return f"获取语音列表失败: {e}"

    @staticmethod
    def _success_msg(text: str) -> str:
        snippet = text[:80]
        suffix = "..." if len(text) > 80 else ""
        return f"已朗读: {snippet}{suffix}"
