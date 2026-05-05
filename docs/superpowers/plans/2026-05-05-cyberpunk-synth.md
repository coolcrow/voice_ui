# 赛博朋克音效交互 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 Voice UI MCP Server 添加 Blade Runner 风格赛博朋克音效和消息风格化。

**Architecture:** 新增 `synth.py`（音效合成器）和 `style.py`（消息风格化），在 MCP Server 层通过装饰器包装 TTS 调用，零外部依赖。

**Tech Stack:** Python 3.10+, struct/wave（标准库）, 现有 `engines/_playback.py`

**Spec:** `docs/superpowers/specs/2026-05-05-cyberpunk-synth-design.md`

---

## File Structure

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `src/voice_ui/synth.py` | 音效合成器：生成 WAV 并播放 |
| Create | `src/voice_ui/style.py` | 赛博朋克风格消息文案 |
| Create | `tests/test_synth.py` | 音效生成测试（不播放） |
| Create | `tests/test_style.py` | 消息风格化测试 |
| Modify | `src/voice_ui/mcp_server.py` | 集成音效包装、启动仪式、消息风格化 |
| Modify | `voice_config.json` | 新增 `synth` 配置段 |
| Modify | `tests/test_mcp_server.py` | 适配 notify event 参数、风格化返回 |
| Modify | `tests/conftest.py` | SAMPLE_CONFIG 新增 synth 配置 |

---

### Task 1: 创建 style.py 消息风格化模块

**Files:**
- Create: `src/voice_ui/style.py`
- Test: `tests/test_style.py`

- [ ] **Step 1: 写 style.py 测试**

创建 `tests/test_style.py`：

```python
"""style.py 消息风格化测试"""

from voice_ui.style import format_result, TX_OK, TX_NULL, TX_ERR, TX_TIMEOUT


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


class TestConstants:
    def test_tx_ok_has_placeholder(self):
        assert "{text}" in TX_OK

    def test_all_have_prefix(self):
        for const in [TX_OK, TX_NULL, TX_ERR, TX_TIMEOUT]:
            assert "[VOICE::" in const
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /Users/smilerz/PycharmProjects/voice_ui && source .venv/bin/activate && pytest tests/test_style.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'voice_ui.style'`

- [ ] **Step 3: 写 style.py 实现**

创建 `src/voice_ui/style.py`：

```python
"""赛博朋克风格消息文案"""

TX_OK = "[VOICE::TX] 信号已发出 → {text}"
TX_NULL = "[VOICE::NULL] 空载波，传输终止"
TX_ERR = "[VOICE::ERR] 传输中断"
TX_TIMEOUT = "[VOICE::TIMEOUT] 信号衰减"
SCAN_HEADER = "[VOICE::SCAN] 频段扫描结果"
BOOT_TITLE = "[VOICE::SYS] ═══ 语音矩阵已上线 ═══"
BOOT_STATUS = "[VOICE::SYS] 信号锁定 · 频段正常 · 等待指令"


def format_result(raw: str) -> str:
    """将引擎原始返回映射为赛博朋克风格文案。"""
    if not raw:
        return TX_NULL

    if "为空" in raw or "跳过" in raw:
        return TX_NULL
    if raw == "朗读失败":
        return TX_ERR
    if "超时" in raw:
        return TX_TIMEOUT
    if "已朗读" in raw:
        snippet = raw.replace("已朗读: ", "").replace("已朗读:", "")
        if len(snippet) > 60:
            snippet = snippet[:60] + "..."
        return TX_OK.format(text=snippet)
    if "可用语音" in raw or "voice" in raw.lower():
        return raw.replace("edge-tts 可用语音", SCAN_HEADER).replace("可用语音", SCAN_HEADER)
    if "无可用" in raw:
        return "[VOICE::ERR] 频段扫描失败"

    return raw
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd /Users/smilerz/PycharmProjects/voice_ui && source .venv/bin/activate && pytest tests/test_style.py -v`
Expected: 7 passed

- [ ] **Step 5: 提交**

```bash
git add src/voice_ui/style.py tests/test_style.py
git commit -m "feat: add cyberpunk message styling module"
```

---

### Task 2: 创建 synth.py 音效合成器

**Files:**
- Create: `src/voice_ui/synth.py`
- Test: `tests/test_synth.py`

- [ ] **Step 1: 写 synth.py 测试**

创建 `tests/test_synth.py`：

```python
"""synth.py 音效合成器测试"""

import struct
import wave

import pytest

from voice_ui.synth import SynthEngine


@pytest.fixture
def synth() -> SynthEngine:
    return SynthEngine({"synth": {"enabled": True, "volume": 0.3}})


@pytest.fixture
def synth_disabled() -> SynthEngine:
    return SynthEngine({"synth": {"enabled": False}})


def _read_wav(path: str) -> wave.Wave_read:
    return wave.open(path, "rb")


class TestSynthGenerate:
    @pytest.mark.parametrize("sound_type", [
        "boot", "pre_speak", "post_speak", "success", "error", "warning",
    ])
    def test_generate_returns_valid_wav(self, synth: SynthEngine, sound_type: str):
        path = synth.generate(sound_type)
        with _read_wav(path) as w:
            assert w.getnchannels() == 1
            assert w.getsampwidth() == 2
            assert w.getframerate() == 22050
            assert w.getnframes() > 0

    @pytest.mark.parametrize("sound_type", [
        "boot", "pre_speak", "post_speak", "success", "error", "warning",
    ])
    def test_generate_duration_reasonable(self, synth: SynthEngine, sound_type: str):
        path = synth.generate(sound_type)
        with _read_wav(path) as w:
            duration = w.getnframes() / w.getframerate()
            assert 0.1 < duration < 2.5, f"{sound_type} duration {duration}s out of range"

    def test_volume_affects_amplitude(self):
        loud = SynthEngine({"synth": {"enabled": True, "volume": 1.0}})
        quiet = SynthEngine({"synth": {"enabled": True, "volume": 0.1}})

        path_loud = loud.generate("post_speak")
        path_quiet = quiet.generate("post_speak")

        with _read_wav(path_loud) as w:
            frames_loud = w.readframes(w.getnframes())

        with _read_wav(path_quiet) as w:
            frames_quiet = w.readframes(w.getnframes())

        max_loud = max(abs(struct.unpack("<h", frames_loud[i:i+2])[0])
                       for i in range(0, len(frames_loud), 2))
        max_quiet = max(abs(struct.unpack("<h", frames_quiet[i:i+2])[0])
                        for i in range(0, len(frames_quiet), 2))

        assert max_loud > max_quiet

    def test_unknown_sound_type_raises(self, synth: SynthEngine):
        with pytest.raises(ValueError, match="unknown"):
            synth.generate("nonexistent")

    def test_boot_is_longest(self, synth: SynthEngine):
        boot_dur = self._duration(synth, "boot")
        for st in ["pre_speak", "post_speak", "success", "error", "warning"]:
            assert boot_dur > self._duration(synth, st), f"boot should be longer than {st}"

    def _duration(self, synth: SynthEngine, sound_type: str) -> float:
        path = synth.generate(sound_type)
        with _read_wav(path) as w:
            return w.getnframes() / w.getframerate()


class TestSynthDisabled:
    def test_disabled_play_does_nothing(self, synth_disabled: SynthEngine):
        synth_disabled.play("boot")  # should not raise or play

    def test_disabled_generate_raises(self, synth_disabled: SynthEngine):
        with pytest.raises(RuntimeError, match="disabled"):
            synth_disabled.generate("boot")
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /Users/smilerz/PycharmProjects/voice_ui && source .venv/bin/activate && pytest tests/test_synth.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'voice_ui.synth'`

- [ ] **Step 3: 写 synth.py 实现**

创建 `src/voice_ui/synth.py`：

```python
"""赛博朋克音效合成器 — 纯 Python 生成 WAV 音效"""

import math
import os
import struct
import tempfile
import wave
from typing import List, Tuple

SAMPLE_RATE = 22050
SAMPLE_WIDTH = 2  # 16bit
NUM_CHANNELS = 1


class SynthEngine:
    """生成赛博朋克风格合成器音效。"""

    _SOUND_DEFS = {
        "boot": "boot",
        "pre_speak": "pre_speak",
        "post_speak": "post_speak",
        "success": "success",
        "error": "error",
        "warning": "warning",
    }

    def __init__(self, config: dict) -> None:
        synth_cfg = config.get("synth", {})
        self.enabled = synth_cfg.get("enabled", True)
        self.volume = synth_cfg.get("volume", 0.3)
        self.cfg_boot = synth_cfg.get("boot", True)
        self.cfg_pre_speak = synth_cfg.get("pre_speak", True)
        self.cfg_post_speak = synth_cfg.get("post_speak", True)

    def play(self, sound_type: str) -> None:
        """生成并播放音效。"""
        if not self.enabled:
            return
        if not self._check_config(sound_type):
            return

        from ._playback import play_audio_file

        path = self.generate(sound_type)
        try:
            play_audio_file(path)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def generate(self, sound_type: str) -> str:
        """生成 WAV 文件，返回路径。"""
        if not self.enabled:
            raise RuntimeError("synth disabled")

        if sound_type not in self._SOUND_DEFS:
            raise ValueError(f"unknown sound type: {sound_type}")

        generator = getattr(self, f"_gen_{sound_type}")
        samples = generator()
        return self._write_wav(samples)

    def _check_config(self, sound_type: str) -> bool:
        if sound_type == "boot" and not self.cfg_boot:
            return False
        if sound_type == "pre_speak" and not self.cfg_pre_speak:
            return False
        if sound_type == "post_speak" and not self.cfg_post_speak:
            return False
        return True

    # --- 波形生成器 ---

    @staticmethod
    def _sine(freq: float, t: float) -> float:
        return math.sin(2 * math.pi * freq * t)

    @staticmethod
    def _square(freq: float, t: float) -> float:
        return 1.0 if SynthEngine._sine(freq, t) >= 0 else -1.0

    @staticmethod
    def _sawtooth(freq: float, t: float) -> float:
        return 2.0 * (freq * t % 1.0) - 1.0

    @staticmethod
    def _triangle(freq: float, t: float) -> float:
        return 2.0 * abs(2.0 * (freq * t % 1.0) - 1.0) - 1.0

    def _envelope(self, t: float, duration: float,
                  attack: float = 0.01, release: float = 0.05) -> float:
        """简单 attack/release 包络。"""
        if t < attack:
            return t / attack
        if t > duration - release:
            return (duration - t) / release
        return 1.0

    def _apply_volume(self, samples: List[float]) -> List[int]:
        """浮点采样 → 16bit 整数，施加音量。"""
        result = []
        for s in samples:
            clamped = max(-1.0, min(1.0, s * self.volume))
            result.append(int(clamped * 32767))
        return result

    # --- 音效定义 ---

    def _gen_boot(self) -> List[float]:
        """启动序列：低频扫频到高频 + 稳定尾音。"""
        samples: List[float] = []
        sweep_dur = 1.0
        tail_dur = 0.5

        # 扫频 120→880Hz
        n_sweep = int(SAMPLE_RATE * sweep_dur)
        for i in range(n_sweep):
            t = i / SAMPLE_RATE
            progress = t / sweep_dur
            freq = 120 + (880 - 120) * progress
            env = self._envelope(t, sweep_dur, attack=0.05, release=0.1)
            samples.append(self._sine(freq, t) * env)

        # 稳定尾音 880Hz
        n_tail = int(SAMPLE_RATE * tail_dur)
        for i in range(n_tail):
            t = i / SAMPLE_RATE
            env = self._envelope(t, tail_dur, attack=0.01, release=0.3)
            samples.append(self._sine(880, t) * env)

        return samples

    def _gen_pre_speak(self) -> List[float]:
        """朗读前奏：锯齿波 C5→A4 下行两音。"""
        samples: List[float] = []
        note_dur = 0.12
        gap = 0.03

        for freq in [523.25, 440.0]:  # C5, A4
            n = int(SAMPLE_RATE * note_dur)
            for i in range(n):
                t = i / SAMPLE_RATE
                env = self._envelope(t, note_dur, attack=0.005, release=0.03)
                samples.append(self._sawtooth(freq, t) * env)
            # gap
            samples.extend([0.0] * int(SAMPLE_RATE * gap))

        return samples

    def _gen_post_speak(self) -> List[float]:
        """朗读尾声：440Hz 正弦波淡出。"""
        samples: List[float] = []
        duration = 0.4
        n = int(SAMPLE_RATE * duration)

        for i in range(n):
            t = i / SAMPLE_RATE
            env = self._envelope(t, duration, attack=0.01, release=0.3)
            samples.append(self._sine(440, t) * env)

        return samples

    def _gen_success(self) -> List[float]:
        """成功提示：C5→E5→G5 三连音。"""
        samples: List[float] = []
        note_dur = 0.12
        gap = 0.04

        for freq in [523.25, 659.25, 783.99]:  # C5, E5, G5
            n = int(SAMPLE_RATE * note_dur)
            for i in range(n):
                t = i / SAMPLE_RATE
                env = self._envelope(t, note_dur, attack=0.005, release=0.03)
                samples.append(self._sine(freq, t) * env)
            samples.extend([0.0] * int(SAMPLE_RATE * gap))

        return samples

    def _gen_error(self) -> List[float]:
        """错误提示：方波 C3→C2 下行。"""
        samples: List[float] = []
        note_dur = 0.25
        gap = 0.05

        for freq in [130.81, 65.41]:  # C3, C2
            n = int(SAMPLE_RATE * note_dur)
            for i in range(n):
                t = i / SAMPLE_RATE
                env = self._envelope(t, note_dur, attack=0.005, release=0.08)
                samples.append(self._square(freq, t) * env)
            samples.extend([0.0] * int(SAMPLE_RATE * gap))

        return samples

    def _gen_warning(self) -> List[float]:
        """警告提示：三角波 E4 双音重复。"""
        samples: List[float] = []
        note_dur = 0.1
        gap = 0.08

        for _ in range(2):
            n = int(SAMPLE_RATE * note_dur)
            for i in range(n):
                t = i / SAMPLE_RATE
                env = self._envelope(t, note_dur, attack=0.005, release=0.03)
                samples.append(self._triangle(329.63, t) * env)  # E4
            samples.extend([0.0] * int(SAMPLE_RATE * gap))

        return samples

    # --- WAV 输出 ---

    def _write_wav(self, raw_samples: List[float]) -> str:
        """将浮点采样写入临时 WAV 文件。"""
        pcm = self._apply_volume(raw_samples)

        fd, path = tempfile.mkstemp(suffix=".wav")
        try:
            with wave.open(path, "wb") as w:
                w.setnchannels(NUM_CHANNELS)
                w.setsampwidth(SAMPLE_WIDTH)
                w.setframerate(SAMPLE_RATE)
                data = struct.pack(f"<{len(pcm)}h", *pcm)
                w.writeframes(data)
        except Exception:
            os.close(fd)
            raise

        return path
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd /Users/smilerz/PycharmProjects/voice_ui && source .venv/bin/activate && pytest tests/test_synth.py -v`
Expected: 12 passed

- [ ] **Step 5: 提交**

```bash
git add src/voice_ui/synth.py tests/test_synth.py
git commit -m "feat: add cyberpunk synth engine with 6 sound types"
```

---

### Task 3: 更新 voice_config.json 和 conftest.py

**Files:**
- Modify: `voice_config.json`
- Modify: `tests/conftest.py`

- [ ] **Step 1: 更新 voice_config.json，新增 synth 段**

在 `voice_config.json` 的 `"debug": false` 之前插入：

```json
  "synth": {
    "enabled": true,
    "volume": 0.3,
    "boot": true,
    "pre_speak": true,
    "post_speak": true
  },
```

完整文件变为：

```json
{
  "comment": "Claude Code 语音输出配置",

  "tts_engine": "edge-tts",
  "fallback_engine": "system",
  "speed": 0.8,
  "voice": "",

  "engines": {
    "system": {
      "enabled": true
    },
    "edge-tts": {
      "enabled": true,
      "default_voice": "zh-CN-XiaoxiaoNeural",
      "default_rate": 180
    },
    "pyttsx3": {
      "enabled": false,
      "default_voice": "",
      "default_rate": 180
    },
    "openai": {
      "enabled": false,
      "default_voice": "alloy",
      "model": "tts-1"
    },
    "kokoro": {
      "enabled": false,
      "default_voice": "zf_xiaobei",
      "lang_code": "z"
    }
  },

  "synth": {
    "enabled": true,
    "volume": 0.3,
    "boot": true,
    "pre_speak": true,
    "post_speak": true
  },

  "debug": false
}
```

- [ ] **Step 2: 更新 conftest.py SAMPLE_CONFIG，新增 synth 配置并移除管道模式残留字段**

将 `tests/conftest.py` 中 `SAMPLE_CONFIG` 替换为：

```python
SAMPLE_CONFIG: Dict = {
    "tts_engine": "edge-tts",
    "fallback_engine": "system",
    "speed": 0.8,
    "voice": "",
    "debug": False,
    "engines": {
        "edge-tts": {
            "enabled": True,
            "default_voice": "zh-CN-XiaoxiaoNeural",
        },
        "system": {"enabled": True},
    },
    "synth": {
        "enabled": True,
        "volume": 0.3,
        "boot": True,
        "pre_speak": True,
        "post_speak": True,
    },
}
```

移除的字段：`speak_triggers`、`silence_triggers`、`code_patterns`、`min_interval_seconds`、`max_speak_per_minute`、`startup_beep`（管道模式残留）。

- [ ] **Step 3: 运行全部测试确认无回归**

Run: `cd /Users/smilerz/PycharmProjects/voice_ui && source .venv/bin/activate && pytest tests/ -v`
Expected: 所有测试通过

- [ ] **Step 4: 提交**

```bash
git add voice_config.json tests/conftest.py
git commit -m "chore: add synth config, remove pipe-mode config remnants"
```

---

### Task 4: 改造 mcp_server.py — 集成音效和风格化

**Files:**
- Modify: `src/voice_ui/mcp_server.py`
- Modify: `tests/test_mcp_server.py`

- [ ] **Step 1: 写 mcp_server 集成测试**

替换 `tests/test_mcp_server.py` 全部内容为：

```python
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
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd /Users/smilerz/PycharmProjects/voice_ui && source .venv/bin/activate && pytest tests/test_mcp_server.py -v`
Expected: FAIL — speak 返回 "已朗读" 但测试期望 "[VOICE::TX]"

- [ ] **Step 3: 改造 mcp_server.py**

替换 `src/voice_ui/mcp_server.py` 全部内容为：

```python
#!/usr/bin/env python3
"""Voice TTS MCP Server

赛博朋克风格语音输出 — 信号锁定 · 频段正常 · 等待指令。

配置（在 .claude/settings.json 中添加）:
{
  "mcpServers": {
    "voice-tts": {
      "command": "/path/to/voice_ui/.venv/bin/python",
      "args": ["-m", "voice_ui.mcp_server"]
    }
  }
}
"""

import sys

from mcp.server.fastmcp import FastMCP

from .style import BOOT_STATUS, BOOT_TITLE, format_result
from .synth import SynthEngine
from .tts import TTSProvider

mcp = FastMCP("voice-tts")

_provider: TTSProvider | None = None
_synth: SynthEngine | None = None
_config: dict = {}


def _get_provider() -> TTSProvider:
    global _provider
    if _provider is None:
        from .config import load_config

        _config.update(load_config())
        _provider = TTSProvider(_config)
    return _provider


def _get_synth() -> SynthEngine:
    global _synth
    if _synth is None:
        if not _config:
            from .config import load_config

            _config.update(load_config())
        _synth = SynthEngine(_config)
    return _synth


def _boot() -> None:
    """赛博朋克启动仪式。"""
    print(f"\n{BOOT_TITLE}", file=sys.stderr)
    print(BOOT_STATUS, file=sys.stderr)
    _get_synth().play("boot")


@mcp.tool()
def speak(text: str, voice: str = "", rate: int = 180) -> str:
    """朗读文本内容。当你想用语音通知用户重要信息时调用此工具。

    Args:
        text: 要朗读的文本内容
        voice: 语音名称（各引擎有不同的语音列表，可用 list_voices 查看）
        rate: 语速（每分钟词数，默认 180）
    """
    synth = _get_synth()
    synth.play("pre_speak")
    raw = _get_provider().speak_sync(text, voice=voice, rate=rate)
    synth.play("post_speak")
    return format_result(raw)


@mcp.tool()
def notify(text: str, event: str = "") -> str:
    """发送简短语音通知。适合读一句话的摘要，如任务完成、发现错误等。

    Args:
        text: 通知内容（建议 50 字以内）
        event: 事件类型 "success" / "error" / "warning"，不传用默认音效
    """
    synth = _get_synth()
    if event in ("success", "error", "warning"):
        synth.play(event)
    else:
        synth.play("pre_speak")

    raw = _get_provider().speak_sync(text)
    synth.play("post_speak")
    return format_result(raw)


@mcp.tool()
def list_voices() -> str:
    """列出当前 TTS 引擎可用的语音。"""
    raw = _get_provider().list_voices()
    return format_result(raw)


if __name__ == "__main__":
    _boot()
    mcp.run()
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd /Users/smilerz/PycharmProjects/voice_ui && source .venv/bin/activate && pytest tests/test_mcp_server.py -v`
Expected: 8 passed

- [ ] **Step 5: 运行全部测试确认无回归**

Run: `cd /Users/smilerz/PycharmProjects/voice_ui && source .venv/bin/activate && pytest tests/ -v`
Expected: 所有测试通过

- [ ] **Step 6: 提交**

```bash
git add src/voice_ui/mcp_server.py tests/test_mcp_server.py
git commit -m "feat: integrate cyberpunk synth and styling into MCP server"
```

---

### Task 5: 端到端验证

**Files:** 无新文件

- [ ] **Step 1: 运行完整测试套件**

Run: `cd /Users/smilerz/PycharmProjects/voice_ui && source .venv/bin/activate && pytest tests/ -v --tb=short`
Expected: 全部通过

- [ ] **Step 2: 手动验证 MCP server 启动音效**

Run: `cd /Users/smilerz/PycharmProjects/voice_ui && source .venv/bin/activate && timeout 5 python -c "from voice_ui.mcp_server import _boot; _boot()" 2>&1`
Expected: 听到启动扫频音效，stderr 输出欢迎语

- [ ] **Step 3: 手动验证 speak 音效包装**

Run: `cd /Users/smilerz/PycharmProjects/voice_ui && source .venv/bin/activate && python -c "
from unittest.mock import patch
from voice_ui.mcp_server import _get_provider, _get_synth
provider = _get_provider()
synth = _get_synth()
# Play pre_speak sound
synth.play('pre_speak')
print('pre_speak done')
synth.play('post_speak')
print('post_speak done')
synth.play('success')
print('success done')
synth.play('error')
print('error done')
synth.play('warning')
print('warning done')
"`
Expected: 依次听到5种不同音效

- [ ] **Step 4: 最终提交（如有遗漏修复）**

```bash
git add -A
git commit -m "chore: e2e verification complete"
```

---

## Self-Review

**1. Spec 覆盖检查：**
- SynthEngine 6 种音效 → Task 2 ✓
- style.py 消息风格化 → Task 1 ✓
- MCP server 启动仪式 → Task 4 `_boot()` ✓
- 朗读包装 pre/post speak → Task 4 `speak()` 和 `notify()` ✓
- notify event 参数 → Task 4 `notify(event=)` ✓
- 返回消息风格化 → Task 4 所有 tool 函数出口 ✓
- voice_config.json synth 配置 → Task 3 ✓
- 不改动 engines/hook_handler → 确认无涉及 ✓

**2. 占位符扫描：** 无 TBD/TODO，所有步骤含完整代码 ✓

**3. 类型一致性：**
- `SynthEngine(config: dict)` 构造签名一致 ✓
- `_get_synth()` 返回 `SynthEngine` ✓
- `notify(event: str = "")` 签名与测试匹配 ✓
- `format_result(raw: str) -> str` 签名一致 ✓
