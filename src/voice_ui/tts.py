"""多引擎 TTS 封装 — 委托给注册表中的引擎实例"""

import sys
import threading
import time
from typing import Dict

from .engines import get_engine, list_available_engines
from .engines._base import TTSEngine


class TTSProvider:
    """多引擎 TTS 封装，支持引擎选择与自动降级。"""

    def __init__(self, config: Dict) -> None:
        self.config = config
        self.speed = config.get("speed", 0.8)
        self.voice = config.get("voice", "")
        self._engine: TTSEngine | None = None
        self._fallback_engine: TTSEngine | None = None
        self._init_engine()

    def _init_engine(self) -> None:
        engine_name = self.config.get("tts_engine", "edge-tts")
        if engine_name == "auto":
            engine_name = "edge-tts"

        try:
            self._engine = get_engine(engine_name, self.config)
        except (ImportError, ValueError) as e:
            print(
                f"[Voice Plugin] 引擎 '{engine_name}' 不可用: {e}，"
                f"降级到 system",
                file=sys.stderr,
            )
            self._engine = self._get_fallback()

        try:
            fallback_name = self.config.get("fallback_engine", "system")
            self._fallback_engine = get_engine(fallback_name, self.config)
        except (ImportError, ValueError):
            pass

    def _get_fallback(self) -> TTSEngine:
        try:
            return get_engine("system", self.config)
        except (ImportError, ValueError):
            from .engines.system import SystemTTSEngine

            return SystemTTSEngine({})

    def speak(self, text: str) -> None:
        """异步非阻塞朗读（用于 pipe/hook 模式）。"""
        if not text or len(text) < 10:
            return

        if (
            hasattr(self, "_last_text")
            and time.time() - getattr(self, "_last_time", 0) < 5
            and getattr(self, "_last_text", "") == text
        ):
            return

        self._last_text = text
        self._last_time = time.time()

        thread = threading.Thread(
            target=self._speak_safe, args=(text,), daemon=True
        )
        thread.start()

    def speak_sync(self, text: str, voice: str = "", rate: int = 180) -> str:
        """同步朗读（用于 MCP 模式），返回状态字符串。"""
        if not text:
            return "文本为空，跳过朗读"

        try:
            return self._engine.speak_sync(text, voice=voice, rate=rate)
        except Exception:
            if self._fallback_engine and self._engine.name != "system":
                try:
                    return self._fallback_engine.speak_sync(
                        text, voice="", rate=rate
                    )
                except Exception:
                    pass
            return "朗读失败"

    def list_voices(self) -> str:
        """列出当前引擎的可用语音。"""
        if self._engine:
            return self._engine.list_voices()
        return "无可用引擎"

    def _speak_safe(self, text: str) -> None:
        """带降级的异步朗读。"""
        try:
            rate = int(self.speed * 180)
            self._engine.speak_sync(text, voice=self.voice, rate=rate)
        except Exception:
            if self._fallback_engine and self._engine.name != "system":
                try:
                    rate = int(self.speed * 180)
                    self._fallback_engine.speak_sync(
                        text, voice=self.voice, rate=rate
                    )
                except Exception:
                    print(
                        "[Voice Plugin] 降级引擎也失败",
                        file=sys.stderr,
                    )
