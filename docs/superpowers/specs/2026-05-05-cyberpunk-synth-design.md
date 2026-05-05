# 赛博朋克音效交互设计

> 日期: 2026-05-05
> 状态: 待审核

## 目标

为 Voice UI MCP Server 添加 Blade Runner 风格赛博朋克音效和消息风格化，提升交互的仪式感和情绪价值。零外部依赖，纯 Python 代码生成合成器音效。

## 方案

新增独立音效模块 `SynthEngine`，在 MCP Server 层包装 TTS 调用，不影响引擎层和 hook_handler。

## 新增模块

### `src/voice_ui/synth.py` — 音效合成器

零外部依赖（仅 `struct`、`wave`、`tempfile`），16bit mono 22050Hz 生成，临时文件播放后即删。

音效定义：

| 类型 | 波形 | 描述 | 时长 |
|------|------|------|------|
| `boot` | 正弦波扫频 120→880Hz + 稳定尾音 | 启动序列 | ~1.5s |
| `pre_speak` | 锯齿波 C5→A4 下行两音 | 朗读前奏 | ~0.3s |
| `post_speak` | 正弦波 440Hz 淡出 | 朗读尾声 | ~0.4s |
| `success` | 正弦波 C5→E5→G5 三连音 | 成功事件 | ~0.5s |
| `error` | 方波 C3→C2 下行 | 错误事件 | ~0.6s |
| `warning` | 三角波 E4 双音重复 | 警告事件 | ~0.4s |

接口：

```python
class SynthEngine:
    def __init__(self, config: dict) -> None
    def play(self, sound_type: str) -> None        # 生成并播放
    def generate(self, sound_type: str) -> str      # 生成 wav 返回路径
```

音量由 config `synth.volume` 控制（0.0-1.0，默认 0.3）。

### `src/voice_ui/style.py` — 消息风格化

集中管理赛博朋克文案常量：

```python
TX_OK = "[VOICE::TX] 信号已发出 → {text}"
TX_NULL = "[VOICE::NULL] 空载波，传输终止"
TX_ERR = "[VOICE::ERR] 传输中断"
TX_TIMEOUT = "[VOICE::TIMEOUT] 信号衰减"
SCAN_HEADER = "[VOICE::SCAN] 频段扫描结果"
BOOT_TITLE = "[VOICE::SYS] ═══ 语音矩阵已上线 ═══"
BOOT_STATUS = "[VOICE::SYS] 信号锁定 · 频段正常 · 等待指令"
```

提供格式化函数，将引擎原始返回映射为风格化文案。

## 改动模块

### `src/voice_ui/mcp_server.py`

1. **启动仪式** — 服务初始化时播放 `boot` 音效，stderr 输出欢迎语
2. **朗读包装** — 通过装饰器在 `speak`/`notify` 前后插入 `pre_speak`/`post_speak` 音效
3. **返回消息** — 出口处用 `style.py` 包装引擎原始返回
4. **notify 新增 event 参数** — 支持 `success`/`error`/`warning`，播放对应事件音效替代通用 `pre_speak`

notify 接口变更：

```python
@mcp.tool()
def notify(text: str, event: str = "") -> str:
    """发送简短语音通知。

    Args:
        text: 通知内容（建议 50 字以内）
        event: 事件类型 "success" / "error" / "warning"，不传用默认音效
    """
```

speak 接口不变。

### `voice_config.json`

新增 `synth` 配置段：

```json
{
  "synth": {
    "enabled": true,
    "volume": 0.3,
    "boot": true,
    "pre_speak": true,
    "post_speak": true
  }
}
```

## 不改动的部分

- `engines/` — 所有 TTS 引擎不动
- `tts.py` — 引擎封装层不动（除已修复的降级 bug）
- `hook_handler.py` — 不加音效，保持简洁
- `config.py` — 仅读取新增的 synth 配置段，无结构变化

## 音效技术细节

- 采样率 22050Hz，16bit mono，标准 WAV 格式
- 正弦波：`sin(2π * f * t)`，柔和，用于 boot / success / post_speak
- 方波：`sign(sin(2π * f * t))`，刺耳，用于 error
- 锯齿波：`2 * (f * t mod 1) - 1`，有棱角，用于 pre_speak
- 三角波：`2 * |2 * (f * t mod 1) - 1| - 1`，柔和但有质感，用于 warning
- 音量控制：采样值乘以 volume 系数
- ADSR 包络：各音效使用简单的 attack/release 包络避免爆音

## 测试策略

- `tests/test_synth.py` — 测试音效生成（不播放），验证 WAV 文件格式、时长、采样率
- `tests/test_style.py` — 测试消息格式化函数
- 更新 `tests/test_mcp_server.py` — 适配 notify 新增的 event 参数和返回消息风格化
