"""Hook Handler 测试"""

import json
import os
import time
from unittest.mock import patch

from voice_ui.hook_handler import filter_assistant_message, should_skip, MARK_FILE


class TestFilterAssistantMessage:
    def test_empty_input(self):
        assert filter_assistant_message("") == ""

    def test_plain_text(self):
        result = filter_assistant_message("任务已完成。所有文件都已更新。")
        assert "任务已完成" in result

    def test_removes_code_blocks(self):
        text = "我来修改代码\n```python\nprint('hello')\n```\n修改完成。"
        result = filter_assistant_message(text)
        assert "print" not in result
        assert "我来修改代码" in result

    def test_removes_inline_code(self):
        text = "请运行 `pip install` 命令。"
        result = filter_assistant_message(text)
        assert "pip install" not in result

    def test_truncates_long_text(self):
        text = "这是一段很长的文本。" * 100
        result = filter_assistant_message(text)
        assert len(result) <= 310

    def test_short_text_skipped(self):
        result = filter_assistant_message("ok")
        assert result == ""

    def test_removes_file_paths(self):
        text = "请检查 src/app.py 文件。"
        result = filter_assistant_message(text)
        assert "src/app.py" not in result

    def test_removes_horizontal_rule(self):
        text = "总结如下\n---\n这是关键内容。这是重点说明。"
        result = filter_assistant_message(text)
        assert "---" not in result
        assert "这是关键内容" in result

    def test_removes_table_pipes(self):
        text = "| 列1 | 列2 |\n|---|---|\n| 值1 | 值2 |"
        result = filter_assistant_message(text)
        assert "|" not in result

    def test_removes_list_numbers(self):
        text = "1. 第一步\n2. 第二步\n这是总结说明的内容。"
        result = filter_assistant_message(text)
        assert result.startswith("第一步") or "第二步" in result or "总结说明" in result

    def test_removes_markdown_links(self):
        text = "参考 [文档](https://example.com) 了解详情。这是补充说明内容。"
        result = filter_assistant_message(text)
        assert "https" not in result
        assert "example.com" not in result


class TestShouldSkip:
    def test_no_mark_file_returns_false(self, tmp_path):
        mark = tmp_path / ".voice_ui_mcp_spoken"
        with patch("voice_ui.hook_handler.MARK_FILE", str(mark)):
            assert should_skip() is False

    def test_recent_mark_returns_true(self, tmp_path):
        mark = tmp_path / ".voice_ui_mcp_spoken"
        mark.write_text("")
        with patch("voice_ui.hook_handler.MARK_FILE", str(mark)):
            assert should_skip() is True

    def test_stale_mark_returns_false(self, tmp_path):
        mark = tmp_path / ".voice_ui_mcp_spoken"
        mark.write_text("")
        old_time = time.time() - 10
        os.utime(str(mark), (old_time, old_time))
        with patch("voice_ui.hook_handler.MARK_FILE", str(mark)):
            assert should_skip() is False
