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
        "waiting",
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
        "waiting",
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
        for st in ["pre_speak", "post_speak", "success", "error", "warning", "waiting"]:
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


class TestSynthCache:
    def test_same_sound_returns_cached_path(self, synth: SynthEngine):
        path1 = synth.generate("post_speak")
        path2 = synth.generate("post_speak")
        assert path1 == path2

    def test_different_sounds_return_different_paths(self, synth: SynthEngine):
        path1 = synth.generate("success")
        path2 = synth.generate("error")
        assert path1 != path2

    def test_cache_file_exists(self, synth: SynthEngine):
        import os
        path = synth.generate("boot")
        assert os.path.exists(path)
