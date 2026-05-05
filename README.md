# Voice UI

Claude Code 智能语音输出插件 — 只读重要内容，不念代码。

提供两种集成方式：Hooks 模式、MCP Server 模式。

## 项目结构

```
voice_ui/
├── pyproject.toml            # 项目配置 & 依赖
├── voice_config.json         # 语音输出配置
├── src/voice_ui/
│   ├── config.py             # 配置加载
│   ├── tts.py                # 多平台 TTS 引擎
│   ├── hook_handler.py       # 方案1: Claude Code Hooks 处理器
│   └── mcp_server.py         # 方案2: MCP Server（speak/notify 工具）
└── tests/
```

## 快速开始

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## 使用方式

### Hooks 模式

Claude Code 原生 Hooks 机制，在 `Stop` 事件时拿到结构化的 `last_assistant_message`，自动过滤代码块后朗读。

在 `~/.claude/settings.json` 或项目的 `.claude/settings.json` 中添加：

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/voice_ui/.venv/bin/python -m voice_ui.hook_handler"
          }
        ]
      }
    ]
  }
}
```

优点：结构化数据、零误判代码、不干扰终端输出。
缺点：只在 Claude 回复结束时触发，不能实时朗读中间过程。

### MCP Server 模式（推荐）

把 `speak` 和 `notify` 作为工具暴露给 Claude，Claude 自己决定什么时候该朗读。

在 `~/.claude/settings.json` 中添加：

```json
{
  "mcpServers": {
    "voice-tts": {
      "command": "/path/to/voice_ui/.venv/bin/python",
      "args": ["-m", "voice_ui.mcp_server"]
    }
  }
}
```

Claude 将获得以下工具：
- `speak(text, voice?, rate?)` — 朗读指定文本
- `notify(text)` — 发送简短语音通知
- `list_voices()` — 列出系统可用语音

优点：Claude 自主判断朗读时机，准确度最高，可交互式使用。
缺点：Claude 需要主动调用工具，增加一次 tool call 开销。

## 方案对比

| | Hooks 模式 | MCP Server |
|---|---|---|
| 触发方式 | 事件驱动 | Claude 主动调用 |
| 过滤准确度 | 中 | 高 |
| 实时性 | 回复结束时 | 按需 |
| 配置复杂度 | 中 | 低 |
| 对话侵入性 | 无 | 多一次 tool call |
