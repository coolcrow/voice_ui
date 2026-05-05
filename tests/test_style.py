"""style.py 消息风格化测试"""

from voice_ui.style import (
    format_result,
    TX_OK,
    TX_NULL,
    TX_ERR,
    TX_TIMEOUT,
    SCAN_HEADER,
    BOOT_TITLE,
    BOOT_STATUS,
)


class TestFormatResult:
    def test_ok_wraps_text(self):
        result = format_result("已朗读: 测试内容")
        assert result.startswith("[VOICE::TX]")
        assert "测试内容" in result

    def test_ok_truncates_long_text(self):
        long_text = "x" * 200
        result = format_result(f"已朗读: {long_text}")
        assert len(result) < 120

    def test_null_message(self):
        result = format_result("文本为空，跳过朗读")
        assert "[VOICE::NULL]" in result

    def test_error_message(self):
        result = format_result("朗读失败")
        assert "[VOICE::ERR]" in result

    def test_timeout_message(self):
        result = format_result("朗读超时")
        assert "[VOICE::TIMEOUT]" in result

    def test_unknown_passes_through(self):
        result = format_result("edge-tts 可用语音 (显示 30/322)")
        assert "[VOICE::SCAN]" in result

    def test_no_engine_message(self):
        result = format_result("无可用引擎")
        assert "[VOICE::ERR]" in result


class TestConstants:
    def test_tx_ok_has_placeholder(self):
        assert "{text}" in TX_OK

    def test_all_have_prefix(self):
        for const in [TX_OK, TX_NULL, TX_ERR, TX_TIMEOUT, SCAN_HEADER,
                      BOOT_TITLE, BOOT_STATUS]:
            assert "[VOICE::" in const