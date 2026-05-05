"""Kokoro TTS 引擎 — 开源轻量神经网络 TTS（ONNX 推理）"""

import os
import tempfile

from ._base import TTSEngine
from ._playback import play_audio_file
from . import register_engine


@register_engine
class KokoroEngine(TTSEngine):
    """使用 Kokoro ONNX 神经网络进行高质量离线语音合成。"""

    _engine_name = "kokoro"

    @property
    def name(self) -> str:
        return self._engine_name

    def __init__(self, config: dict) -> None:
        self.config = config
        self.default_voice = config.get("default_voice", "zf_xiaobei")
        self.lang_code = config.get("lang_code", "z")
        self._pipeline = None

    def speak_sync(self, text: str, voice: str = "", rate: int = 180) -> str:
        if not text:
            return "文本为空，跳过朗读"

        try:
            import numpy as np
            from kokoro import KPipeline
            import soundfile as sf
        except ImportError:
            raise ImportError(
                "kokoro/soundfile 未安装。请运行: pip install -e '.[kokoro]'"
            )

        if self._pipeline is None:
            self._pipeline = KPipeline(lang_code=self.lang_code)

        voice = voice or self.default_voice

        audio_segments = []
        for _, _, audio in self._pipeline(text, voice=voice):
            audio_segments.append(audio)

        if not audio_segments:
            return "未生成音频"

        full_audio = np.concatenate(audio_segments)

        # 简单变速：通过重采样模拟 rate 调整
        if rate != 180:
            factor = 180 / rate
            indices = np.arange(0, len(full_audio), factor).astype(int)
            indices = indices[indices < len(full_audio)]
            full_audio = full_audio[indices]

        tmp_path = tempfile.mktemp(suffix=".wav")
        try:
            sf.write(tmp_path, full_audio, 24000)
            play_audio_file(tmp_path)
            return self._success_msg(text)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def list_voices(self) -> str:
        return (
            "Kokoro 可用语音 (部分):\n"
            "- zf_xiaobei (中文女声)\n"
            "- zm_yunjian (中文男声)\n"
            "- af_bella (英文女声)\n"
            "- am_adam (英文男声)\n"
            "- bf_emma (英式女声)\n"
            "- bm_george (英式男声)"
        )

    @staticmethod
    def _success_msg(text: str) -> str:
        snippet = text[:80]
        suffix = "..." if len(text) > 80 else ""
        return f"已朗读: {snippet}{suffix}"
