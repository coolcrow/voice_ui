"""TTSProvider 测试"""

from unittest.mock import MagicMock, patch

from voice_ui.tts import TTSProvider


class TestTTSProvider:
    """TTSProvider 单元测试"""

    def test_speak_short_text_ignored(self, config):
        tts = TTSProvider(config)
        tts.speak("hi")

    def test_speak_empty_text_ignored(self, config):
        tts = TTSProvider(config)
        tts.speak("")

    def test_speak_sync_empty_text(self, config):
        tts = TTSProvider(config)
        result = tts.speak_sync("")
        assert "为空" in result or "跳过" in result

    def test_fallback_to_system_on_missing_engine(self, config):
        config["tts_engine"] = "nonexistent"
        tts = TTSProvider(config)
        assert tts._engine is not None
        assert tts._engine.name == "system"

    def test_auto_resolves_to_edge_tts(self, config):
        config["tts_engine"] = "auto"
        with patch(
            "voice_ui.engines.get_engine"
        ) as mock_get:
            mock_engine = MagicMock()
            mock_engine.name = "edge-tts"
            mock_get.return_value = mock_engine
            tts = TTSProvider(config)
            assert tts._engine.name == "edge-tts"

    def test_list_voices_returns_string(self, config):
        tts = TTSProvider(config)
        result = tts.list_voices()
        assert isinstance(result, str)
