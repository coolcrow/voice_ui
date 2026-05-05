"""共享音频播放工具"""

import shutil
import subprocess


def play_audio_file(path: str, timeout: int = 30) -> bool:
    """使用系统可用的播放器播放音频文件。"""
    players = {
        "afplay": [path],
        "ffplay": ["-nodisp", "-autoexit", "-quiet", path],
        "mpv": ["--no-video", "--quiet", path],
    }
    for name, args in players.items():
        if shutil.which(name):
            result = subprocess.run(
                [name] + args,
                capture_output=True,
                timeout=timeout,
            )
            return result.returncode == 0

    raise RuntimeError(
        "未找到音频播放器，请安装 afplay、ffplay 或 mpv"
    )
