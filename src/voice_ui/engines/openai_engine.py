"""OpenAI TTS 引擎 — 使用 OpenAI API 生成高质量语音"""

import os
import tempfile

from ._base import TTSEngine
from ._playback import play_audio_file
from . import register_engine


@register_engine
class OpenAITTSEngine(TTSEngine):
    """使用 OpenAI TTS API (tts-1) 生成语音。"""

    _engine_name = "openai"

    @property
    def name(self) -> str:
        return self._engine_name

    def __init__(self, config: dict) -> None:
        self.config = config
        self.model = config.get("model", "tts-1")
        self.default_voice = config.get("default_voice", "alloy")

    def speak_sync(self, text: str, voice: str = "", rate: int = 180) -> str:
        if not text:
            return "文本为空，跳过朗读"

        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai 未安装。请运行: pip install -e '.[openai]'"
            )

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return "错误: 未设置 OPENAI_API_KEY 环境变量"

        client = OpenAI()
        voice = voice or self.default_voice
        speed = max(0.5, min(4.0, rate / 180))

        response = client.audio.speech.create(
            model=self.model,
            voice=voice,
            input=text,
            speed=speed,
        )

        tmp_path = tempfile.mktemp(suffix=".mp3")
        try:
            response.stream_to_file(tmp_path)
            play_audio_file(tmp_path)
            return self._success_msg(text)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def list_voices(self) -> str:
        return (
            "OpenAI TTS 可用语音:\n"
            "- alloy (中性)\n"
            "- echo (男性)\n"
            "- fable (英式)\n"
            "- onyx (深沉男性)\n"
            "- nova (女性)\n"
            "- shimmer (柔和女性)"
        )

    @staticmethod
    def _success_msg(text: str) -> str:
        snippet = text[:80]
        suffix = "..." if len(text) > 80 else ""
        return f"已朗读: {snippet}{suffix}"
