"""pytest 配置和公共 fixtures"""

import json
from pathlib import Path
from typing import Dict

import pytest

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


@pytest.fixture
def config() -> Dict:
    """返回测试用配置"""
    return SAMPLE_CONFIG.copy()


@pytest.fixture
def config_file(tmp_path: Path, config: Dict) -> Path:
    """创建临时配置文件"""
    cfg = tmp_path / "voice_config.json"
    cfg.write_text(json.dumps(config, ensure_ascii=False))
    return cfg
