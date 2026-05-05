"""MCP Server 测试"""

from unittest.mock import MagicMock, patch

from voice_ui.tts import TTSProvider


class TestMCPSpeakSync:
    """MCP speak 工具测试"""

    def test_empty_text(self, config):
        with patch("voice_ui.mcp_server._get_provider") as mock_get:
            provider = TTSProvider(config)
            mock_get.return_value = provider
            from voice_ui.mcp_server import speak

            result = speak("", voice="", rate=180)
            assert "[VOICE::NULL]" in result

    def test_normal_text(self, config):
        with patch("voice_ui.mcp_server._get_provider") as mock_get:
            provider = TTSProvider(config)
            mock_get.return_value = provider
            with patch.object(provider._engine, "speak_sync") as mock_speak:
                mock_speak.return_value = "已朗读: 测试语音"
                from voice_ui.mcp_server import speak

                result = speak("测试语音", voice="", rate=180)
                assert "[VOICE::TX]" in result

    def test_speak_plays_pre_and_post(self, config):
        with patch("voice_ui.mcp_server._get_provider") as mock_get, \
             patch("voice_ui.mcp_server._get_synth") as mock_synth:
            provider = TTSProvider(config)
            mock_get.return_value = provider
            synth = MagicMock()
            mock_synth.return_value = synth
            with patch.object(provider._engine, "speak_sync") as mock_speak:
                mock_speak.return_value = "已朗读: ok"
                from voice_ui.mcp_server import speak

                speak("ok", voice="", rate=180)
                synth.play.assert_any_call("pre_speak")
                synth.play.assert_any_call("post_speak")


class TestMCPNotify:
    """MCP notify 工具测试"""

    def test_notify_empty(self, config):
        with patch("voice_ui.mcp_server._get_provider") as mock_get:
            provider = TTSProvider(config)
            mock_get.return_value = provider
            from voice_ui.mcp_server import notify

            result = notify("")
            assert "[VOICE::NULL]" in result

    def test_notify_with_event_success(self, config):
        with patch("voice_ui.mcp_server._get_provider") as mock_get, \
             patch("voice_ui.mcp_server._get_synth") as mock_synth:
            provider = TTSProvider(config)
            mock_get.return_value = provider
            synth = MagicMock()
            mock_synth.return_value = synth
            with patch.object(provider._engine, "speak_sync") as mock_speak:
                mock_speak.return_value = "已朗读: done"
                from voice_ui.mcp_server import notify

                result = notify("done", event="success")
                synth.play.assert_any_call("success")
                synth.play.assert_any_call("post_speak")
                assert "[VOICE::TX]" in result

    def test_notify_with_event_error(self, config):
        with patch("voice_ui.mcp_server._get_provider") as mock_get, \
             patch("voice_ui.mcp_server._get_synth") as mock_synth:
            provider = TTSProvider(config)
            mock_get.return_value = provider
            synth = MagicMock()
            mock_synth.return_value = synth
            with patch.object(provider._engine, "speak_sync") as mock_speak:
                mock_speak.return_value = "已朗读: fail"
                from voice_ui.mcp_server import notify

                result = notify("fail", event="error")
                synth.play.assert_any_call("error")

    def test_notify_no_event_uses_pre_speak(self, config):
        with patch("voice_ui.mcp_server._get_provider") as mock_get, \
             patch("voice_ui.mcp_server._get_synth") as mock_synth:
            provider = TTSProvider(config)
            mock_get.return_value = provider
            synth = MagicMock()
            mock_synth.return_value = synth
            with patch.object(provider._engine, "speak_sync") as mock_speak:
                mock_speak.return_value = "已朗读: note"
                from voice_ui.mcp_server import notify

                notify("note")
                synth.play.assert_any_call("pre_speak")
                synth.play.assert_any_call("post_speak")

    def test_notify_with_event_waiting(self, config):
        with patch("voice_ui.mcp_server._get_provider") as mock_get, \
             patch("voice_ui.mcp_server._get_synth") as mock_synth:
            provider = TTSProvider(config)
            mock_get.return_value = provider
            synth = MagicMock()
            mock_synth.return_value = synth
            with patch.object(provider._engine, "speak_sync") as mock_speak:
                mock_speak.return_value = "已朗读: waiting"
                from voice_ui.mcp_server import notify

                result = notify("waiting", event="waiting")
                synth.play.assert_any_call("waiting")
                assert "[VOICE::TX]" in result


class TestMCPListVoices:
    """MCP list_voices 测试"""

    def test_list_voices_styled(self, config):
        with patch("voice_ui.mcp_server._get_provider") as mock_get:
            provider = TTSProvider(config)
            mock_get.return_value = provider
            with patch.object(provider._engine, "list_voices") as mock_lv:
                mock_lv.return_value = "edge-tts 可用语音 (显示 30/322):\n- zh-CN"
                from voice_ui.mcp_server import list_voices

                result = list_voices()
                assert "[VOICE::SCAN]" in result
