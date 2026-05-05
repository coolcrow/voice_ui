"""TTS 引擎抽象基类"""

from abc import ABC, abstractmethod


class TTSEngine(ABC):
    """所有 TTS 引擎的抽象基类。"""

    @property
    @abstractmethod
    def name(self) -> str:
        """引擎标识符。"""

    @abstractmethod
    def speak_sync(self, text: str, voice: str = "", rate: int = 180) -> str:
        """同步朗读文本，返回状态字符串。"""

    @abstractmethod
    def list_voices(self) -> str:
        """返回可用语音列表的格式化字符串。"""
