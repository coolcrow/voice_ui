"""赛博朋克音效合成器 — 纯 Python 生成 WAV 音效"""

import math
import os
import struct
import tempfile
import wave
from typing import List

SAMPLE_RATE = 22050
SAMPLE_WIDTH = 2  # 16bit
NUM_CHANNELS = 1


class SynthEngine:
    """生成赛博朋克风格合成器音效。"""

    _SOUND_TYPES = {"boot", "pre_speak", "post_speak", "success", "error", "warning", "waiting"}

    def __init__(self, config: dict) -> None:
        synth_cfg = config.get("synth", {})
        self.enabled = synth_cfg.get("enabled", True)
        self.volume = synth_cfg.get("volume", 0.3)
        self.cfg_boot = synth_cfg.get("boot", True)
        self.cfg_pre_speak = synth_cfg.get("pre_speak", True)
        self.cfg_post_speak = synth_cfg.get("post_speak", True)
        self._cache: dict[str, str] = {}

    def play(self, sound_type: str) -> None:
        """生成并播放音效。"""
        if not self.enabled:
            return
        if not self._check_config(sound_type):
            return

        from .engines._playback import play_audio_file

        path = self.generate(sound_type)
        try:
            play_audio_file(path)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def generate(self, sound_type: str) -> str:
        """生成 WAV 文件，返回路径（带缓存）。"""
        if not self.enabled:
            raise RuntimeError("synth disabled")

        if sound_type not in self._SOUND_TYPES:
            raise ValueError(f"unknown sound type: {sound_type}")

        if sound_type in self._cache:
            return self._cache[sound_type]

        generator = getattr(self, f"_gen_{sound_type}")
        samples = generator()
        path = self._write_wav(samples)
        self._cache[sound_type] = path
        return path

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
        if t < attack:
            return t / attack
        if t > duration - release:
            return (duration - t) / release
        return 1.0

    def _apply_volume(self, samples: List[float]) -> List[int]:
        result = []
        for s in samples:
            clamped = max(-1.0, min(1.0, s * self.volume))
            result.append(int(clamped * 32767))
        return result

    # --- 音效定义 ---

    def _gen_boot(self) -> List[float]:
        samples: List[float] = []
        sweep_dur = 1.0
        tail_dur = 0.5

        n_sweep = int(SAMPLE_RATE * sweep_dur)
        for i in range(n_sweep):
            t = i / SAMPLE_RATE
            progress = t / sweep_dur
            freq = 120 + (880 - 120) * progress
            env = self._envelope(t, sweep_dur, attack=0.05, release=0.1)
            samples.append(self._sine(freq, t) * env)

        n_tail = int(SAMPLE_RATE * tail_dur)
        for i in range(n_tail):
            t = i / SAMPLE_RATE
            env = self._envelope(t, tail_dur, attack=0.01, release=0.3)
            samples.append(self._sine(880, t) * env)

        return samples

    def _gen_pre_speak(self) -> List[float]:
        samples: List[float] = []
        note_dur = 0.12
        gap = 0.03

        for freq in [523.25, 440.0]:
            n = int(SAMPLE_RATE * note_dur)
            for i in range(n):
                t = i / SAMPLE_RATE
                env = self._envelope(t, note_dur, attack=0.005, release=0.03)
                samples.append(self._sawtooth(freq, t) * env)
            samples.extend([0.0] * int(SAMPLE_RATE * gap))

        return samples

    def _gen_post_speak(self) -> List[float]:
        samples: List[float] = []
        duration = 0.4
        n = int(SAMPLE_RATE * duration)

        for i in range(n):
            t = i / SAMPLE_RATE
            env = self._envelope(t, duration, attack=0.01, release=0.3)
            samples.append(self._sine(440, t) * env)

        return samples

    def _gen_success(self) -> List[float]:
        samples: List[float] = []
        note_dur = 0.12
        gap = 0.04

        for freq in [523.25, 659.25, 783.99]:
            n = int(SAMPLE_RATE * note_dur)
            for i in range(n):
                t = i / SAMPLE_RATE
                env = self._envelope(t, note_dur, attack=0.005, release=0.03)
                samples.append(self._sine(freq, t) * env)
            samples.extend([0.0] * int(SAMPLE_RATE * gap))

        return samples

    def _gen_error(self) -> List[float]:
        samples: List[float] = []
        note_dur = 0.25
        gap = 0.05

        for freq in [130.81, 65.41]:
            n = int(SAMPLE_RATE * note_dur)
            for i in range(n):
                t = i / SAMPLE_RATE
                env = self._envelope(t, note_dur, attack=0.005, release=0.08)
                samples.append(self._square(freq, t) * env)
            samples.extend([0.0] * int(SAMPLE_RATE * gap))

        return samples

    def _gen_warning(self) -> List[float]:
        samples: List[float] = []
        note_dur = 0.1
        gap = 0.08

        for _ in range(2):
            n = int(SAMPLE_RATE * note_dur)
            for i in range(n):
                t = i / SAMPLE_RATE
                env = self._envelope(t, note_dur, attack=0.005, release=0.03)
                samples.append(self._triangle(329.63, t) * env)
            samples.extend([0.0] * int(SAMPLE_RATE * gap))

        return samples

    def _gen_waiting(self) -> List[float]:
        samples: List[float] = []
        note_dur = 0.15
        gap = 0.06

        for freq in [440.0, 554.37, 659.25]:
            n = int(SAMPLE_RATE * note_dur)
            for i in range(n):
                t = i / SAMPLE_RATE
                env = self._envelope(t, note_dur, attack=0.01, release=0.05)
                samples.append(self._triangle(freq, t) * env)
            samples.extend([0.0] * int(SAMPLE_RATE * gap))

        return samples

    # --- WAV 输出 ---

    def _write_wav(self, raw_samples: List[float]) -> str:
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
