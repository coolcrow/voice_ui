"""配置验证测试"""

import pytest

from voice_ui.config import validate_config


class TestValidateConfig:
    def test_valid_config_passes(self):
        config = {
            "tts_engine": "edge-tts",
            "fallback_engine": "system",
            "speed": 0.8,
        }
        errors = validate_config(config)
        assert errors == []

    def test_invalid_engine_name(self):
        config = {
            "tts_engine": "nonexistent-engine",
        }
        errors = validate_config(config)
        assert any("tts_engine" in e for e in errors)

    def test_invalid_fallback_engine(self):
        config = {
            "tts_engine": "edge-tts",
            "fallback_engine": "fake-tts",
        }
        errors = validate_config(config)
        assert any("fallback_engine" in e for e in errors)

    def test_speed_out_of_range(self):
        config = {
            "tts_engine": "edge-tts",
            "speed": 5.0,
        }
        errors = validate_config(config)
        assert any("speed" in e for e in errors)

    def test_negative_speed(self):
        config = {
            "tts_engine": "edge-tts",
            "speed": -0.5,
        }
        errors = validate_config(config)
        assert any("speed" in e for e in errors)

    def test_empty_config_uses_defaults(self):
        errors = validate_config({})
        assert errors == []

    def test_valid_engines(self):
        for engine in ["edge-tts", "system", "pyttsx3", "openai", "kokoro"]:
            config = {"tts_engine": engine}
            errors = validate_config(config)
            assert not any("tts_engine" in e for e in errors), f"{engine} should be valid"
