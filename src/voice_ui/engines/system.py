"""系统原生 TTS 引擎（macOS say / Windows SAPI / Linux espeak）"""

import subprocess
import sys

from ._base import TTSEngine
from . import register_engine


@register_engine
class SystemTTSEngine(TTSEngine):
    """使用操作系统自带 TTS 命令。"""

    _engine_name = "system"

    @property
    def name(self) -> str:
        return self._engine_name

    def __init__(self, config: dict) -> None:
        self.config = config

    def speak_sync(self, text: str, voice: str = "", rate: int = 180) -> str:
        if not text:
            return "文本为空，跳过朗读"

        platform = sys.platform
        try:
            if platform == "darwin":
                cmd = ["say", "-r", str(rate)]
                if voice:
                    cmd.extend(["-v", voice])
                cmd.append(text)
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    return self._success_msg(text)
                return f"朗读失败: {result.stderr.strip()}"

            elif platform == "win32":
                escaped = text.replace('"', '`"')
                ps_cmd = (
                    f'Add-Type -AssemblyName System.Speech; '
                    f'(New-Object System.Speech.Synthesis.SpeechSynthesizer)'
                    f'.Speak("{escaped}")'
                )
                result = subprocess.run(
                    ["powershell", "-Command", ps_cmd],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    return self._success_msg(text)
                return f"朗读失败: {result.stderr.strip()}"

            elif platform == "linux":
                result = subprocess.run(
                    ["espeak", "-s", str(rate), text],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    return self._success_msg(text)
                return f"朗读失败: {result.stderr.strip()}"

            return f"不支持的平台: {platform}"

        except subprocess.TimeoutExpired:
            return "朗读超时"
        except FileNotFoundError as e:
            return f"TTS 引擎未安装: {e}"
        except Exception as e:
            return f"朗读错误: {e}"

    def list_voices(self) -> str:
        platform = sys.platform
        if platform == "darwin":
            try:
                result = subprocess.run(
                    ["say", "-v", "?"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                voices = []
                for line in result.stdout.strip().split("\n"):
                    parts = line.strip().split()
                    if parts:
                        v_name = parts[0]
                        lang = parts[1] if len(parts) > 1 else ""
                        voices.append(f"- {v_name} ({lang})")
                return "可用语音:\n" + "\n".join(voices[:20])
            except Exception as e:
                return f"获取语音列表失败: {e}"

        if platform == "linux":
            try:
                result = subprocess.run(
                    ["espeak", "--voices"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                return f"可用语音:\n{result.stdout.strip()[:500]}"
            except Exception as e:
                return f"获取语音列表失败: {e}"

        return f"当前平台 ({platform}) 暂不支持列出语音"

    @staticmethod
    def _success_msg(text: str) -> str:
        snippet = text[:80]
        suffix = "..." if len(text) > 80 else ""
        return f"已朗读: {snippet}{suffix}"
