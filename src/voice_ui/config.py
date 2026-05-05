"""配置加载"""

import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent.parent / "voice_config.json"

VALID_ENGINES = {"edge-tts", "system", "pyttsx3", "openai", "kokoro"}


def load_config() -> dict:
    """加载并验证配置文件"""
    config_locations = [
        CONFIG_PATH,
        Path.home() / ".voice_ui" / "voice_config.json",
        Path(__file__).parent / "voice_config.json",
    ]
    config: dict = {}
    for path in config_locations:
        if path.exists():
            with open(path, "r") as f:
                config = json.load(f)
            break

    errors = validate_config(config)
    if errors:
        import sys

        for e in errors:
            print(f"[Voice UI] 配置错误: {e}", file=sys.stderr)

    return config


def validate_config(config: dict) -> list[str]:
    """验证配置，返回错误列表。"""
    errors: list[str] = []

    engine = config.get("tts_engine", "edge-tts")
    if engine not in VALID_ENGINES:
        errors.append(f"tts_engine '{engine}' 无效，可选: {', '.join(sorted(VALID_ENGINES))}")

    fallback = config.get("fallback_engine", "system")
    if fallback not in VALID_ENGINES:
        errors.append(f"fallback_engine '{fallback}' 无效，可选: {', '.join(sorted(VALID_ENGINES))}")

    speed = config.get("speed", 0.8)
    if not isinstance(speed, (int, float)) or speed <= 0 or speed > 2.0:
        errors.append(f"speed {speed} 超出范围，应在 (0, 2.0] 之间")

    return errors
