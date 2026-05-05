"""引擎注册表和各引擎单元测试"""

import sys
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from voice_ui.engines import get_engine, list_available_engines
from voice_ui.engines._base import TTSEngine
from voice_ui.engines.system import SystemTTSEngine


class TestEngineRegistry:
    """引擎注册表测试"""

    def test_system_engine_always_registered(self):
        engines = list_available_engines()
        assert "system" in engines

    def test_edge_tts_registered(self):
        engines = list_available_engines()
        assert "edge-tts" in engines

    def test_unknown_engine_raises(self):
        with pytest.raises(ValueError, match="未知引擎"):
            get_engine("nonexistent", {})

    def test_get_system_engine(self):
        engine = get_engine("system", {})
        assert engine.name == "system"

    def test_list_available_returns_list(self):
        engines = list_available_engines()
        assert isinstance(engines, list)
        assert len(engines) >= 2


class TestSystemEngine:
    """SystemTTSEngine 测试"""

    def test_empty_text(self):
        engine = SystemTTSEngine({})
        result = engine.speak_sync("")
        assert "为空" in result or "跳过" in result

    def test_macos_speak(self):
        engine = SystemTTSEngine({})
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = engine.speak_sync("hello world")
            assert "已朗读" in result
            assert mock_run.call_args[0][0][0] == "say"

    def test_macos_speak_with_voice(self):
        engine = SystemTTSEngine({})
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            engine.speak_sync("hello", voice="Samantha", rate=200)
            cmd = mock_run.call_args[0][0]
            assert "-v" in cmd
            assert "Samantha" in cmd

    def test_timeout(self):
        engine = SystemTTSEngine({})
        with patch("subprocess.run") as mock_run:
            import subprocess

            mock_run.side_effect = subprocess.TimeoutExpired("say", 30)
            result = engine.speak_sync("hello")
            assert "超时" in result

    def test_list_voices_macos(self):
        engine = SystemTTSEngine({})
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Samantha    en_US\nDaniel      en_GB\n",
            )
            result = engine.list_voices()
            assert "Samantha" in result


class TestEdgeTTSEngine:
    """EdgeTTSEngine 测试"""

    def test_empty_text(self):
        from voice_ui.engines.edge_tts import EdgeTTSEngine

        engine = EdgeTTSEngine({})
        result = engine.speak_sync("")
        assert "为空" in result or "跳过" in result

    def test_calc_rate(self):
        from voice_ui.engines.edge_tts import EdgeTTSEngine

        assert EdgeTTSEngine._calc_rate(180) == "+0%"
        assert EdgeTTSEngine._calc_rate(200) == "+11%"
        assert EdgeTTSEngine._calc_rate(160) == "-11%"

    def test_import_error(self):
        from voice_ui.engines.edge_tts import EdgeTTSEngine

        engine = EdgeTTSEngine({})
        with patch.dict(sys.modules, {"edge_tts": None}):
            # edge_tts 可能已安装，直接测 ImportError 分支
            with pytest.raises(ImportError, match="edge-tts"):
                # 强制触发 import 路径
                import importlib

                with patch(
                    "builtins.__import__",
                    side_effect=ImportError("No module"),
                ):
                    engine.speak_sync("test")

    def test_default_voice(self):
        from voice_ui.engines.edge_tts import EdgeTTSEngine

        engine = EdgeTTSEngine({})
        assert engine.default_voice == "zh-CN-XiaoxiaoNeural"

    def test_custom_config(self):
        from voice_ui.engines.edge_tts import EdgeTTSEngine

        engine = EdgeTTSEngine(
            {"default_voice": "zh-CN-YunxiNeural", "default_rate": 200}
        )
        assert engine.default_voice == "zh-CN-YunxiNeural"
        assert engine.default_rate == 200


class TestOpenAIEngine:
    """OpenAITTSEngine 测试"""

    def test_list_voices(self):
        from voice_ui.engines.openai_engine import OpenAITTSEngine

        engine = OpenAITTSEngine({})
        result = engine.list_voices()
        assert "alloy" in result
        assert "nova" in result

    def test_no_api_key(self):
        from voice_ui.engines.openai_engine import OpenAITTSEngine

        engine = OpenAITTSEngine({})
        mock_openai = MagicMock()
        with patch.dict("sys.modules", {"openai": mock_openai}):
            with patch.dict("os.environ", {}, clear=True):
                result = engine.speak_sync("test")
                assert "OPENAI_API_KEY" in result

    def test_default_config(self):
        from voice_ui.engines.openai_engine import OpenAITTSEngine

        engine = OpenAITTSEngine({"model": "tts-1-hd"})
        assert engine.model == "tts-1-hd"
        assert engine.default_voice == "alloy"


class TestPyttsx3Engine:
    """Pyttsx3Engine 测试"""

    def test_empty_text(self):
        from voice_ui.engines.pyttsx3_engine import Pyttsx3Engine

        engine = Pyttsx3Engine({})
        result = engine.speak_sync("")
        assert "为空" in result or "跳过" in result


class TestKokoroEngine:
    """KokoroEngine 测试"""

    def test_list_voices(self):
        from voice_ui.engines.kokoro_engine import KokoroEngine

        engine = KokoroEngine({})
        result = engine.list_voices()
        assert "zf_xiaobei" in result

    def test_empty_text(self):
        from voice_ui.engines.kokoro_engine import KokoroEngine

        engine = KokoroEngine({})
        result = engine.speak_sync("")
        assert "为空" in result or "跳过" in result
