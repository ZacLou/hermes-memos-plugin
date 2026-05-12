# hermes-memos-plugin

[English](#english) | [中文](#中文)

---

<a name="english"></a>
# Hermes MemOS Plugin

A memory provider plugin for [Hermes AI Agent](https://github.com/Hermes-ai/hermes) that integrates [MemOS OpenMem API](https://memos-docs.openmem.net) for persistent, intelligent memory across conversations.

## Features

- **Persistent Memory** — Stores conversation facts via MemOS, accessible across sessions
- **Semantic Search** — Retrieve relevant memories by meaning, not keywords
- **Automatic Sync** — Background thread syncs conversations to MemOS without blocking
- **Circuit Breaker** — Graceful degradation when API is unavailable
- **Zero-config** — Works with just an API key, sensible defaults for everything else

## Tools Provided

| Tool | Description |
|------|-------------|
| `memos_profile` | Retrieve all stored memories about the user |
| `memos_search` | Search memories by semantic similarity |
| `memos_conclude` | Store a specific fact about the user |

## Installation

### Prerequisites

- Hermes Agent Gateway installed and running
- A MemOS API key ([get one here](https://memos-docs.openmem.net))

### Install

```bash
# Clone to Hermes plugins directory
git clone https://github.com/ZacJinshare/hermes-memos-plugin.git ~/.hermes/plugins/memos
```

Or manually copy the `memos/` folder to `~/.hermes/plugins/memos/`.

### Configure

Create `~/.hermes/memos.json`:

```json
{
  "api_key": "your-memos-api-key",
  "base_url": "https://memos.memtensor.cn",
  "user_id": "hermes-user",
  "agent_id": "hermes"
}
```

Or use environment variables:

```bash
export MEMOS_API_KEY="your-api-key"
export MEMOS_BASE_URL="https://memos.memtensor.cn"
export MEMOS_USER_ID="hermes-user"
export MEMOS_AGENT_ID="hermes"
```

### Enable in Hermes

Restart the Hermes gateway:

```bash
systemctl --user restart hermes-gateway
```

Check logs to confirm the plugin loaded:

```bash
tail -f ~/.hermes/logs/gateway.log | grep -i memos
```

## Usage

Once installed, the Hermes agent will have access to three new tools:

### `memos_profile`

Get all stored memories about the user. Call this at conversation start.

```
User: hi
Agent: [calls memos_profile]
        "I see we've discussed Python packaging before. Want to continue that?"
```

### `memos_search`

Search memories by meaning:

```
Agent: [calls memos_search with query "user's preferred code style"]
```

### `memos_conclude`

Store an explicit fact:

```
Agent: [calls memos_conclude with conclusion "User prefers single quotes in Python"]
```

## API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `POST /api/openmem/v1/add/message` | Store conversation messages |
| `POST /api/openmem/v1/search/memory` | Semantic search over memories |
| `POST /api/openmem/v1/get/memory` | Retrieve all memories |

## Troubleshooting

**Plugin not loading:**
- Check `~/.hermes/plugins/memos/__init__.py` exists
- Check `~/.hermes/logs/gateway.log` for import errors
- Verify `requests` is installed: `pip install requests`

**API errors:**
- Circuit breaker trips after 5 consecutive failures, cools down for 120s
- Check `/tmp/memos_plugin_debug.log` for detailed debug output
- Verify `api_key` in `~/.hermes/memos.json`

**Debug log not created:**
- Ensure the plugin module parses correctly (no syntax errors)
- Run: `python3 -m py_compile ~/.hermes/plugins/memos/__init__.py`

## Development

```bash
git clone https://github.com/ZacJinshare/hermes-memos-plugin.git
cd hermes-memos-plugin
# Edit memos/__init__.py
# Test by copying to ~/.hermes/plugins/memos/ and restarting Hermes
```

## License

MIT License — see [LICENSE](LICENSE)

## Links

- [Hermes Agent](https://github.com/Hermes-ai/hermes)
- [MemOS Documentation](https://memos-docs.openmem.net)
- [OpenMem API Reference](https://memos.memtensor.cn/docs)

---

<a name="中文"></a>
# Hermes MemOS 插件

为 [Hermes AI Agent](https://github.com/Hermes-ai/hermes) 提供的记忆提供者插件，集成 [MemOS OpenMem API](https://memos-docs.openmem.net)，实现跨对话的持久化智能记忆。

## 功能特性

- **持久化记忆** — 通过 MemOS 存储对话事实，跨会话访问
- **语义搜索** — 按语义（而非关键词）检索相关记忆
- **自动同步** — 后台线程无阻塞同步对话到 MemOS
- **断路器保护** — API 不可用时优雅降级
- **零配置启动** — 只需 API 密钥，其余均有合理默认值

## 提供的工具

| 工具 | 说明 |
|------|------|
| `memos_profile` | 获取用户所有已存储记忆 |
| `memos_search` | 按语义相似度搜索记忆 |
| `memos_conclude` | 存储关于用户的特定事实 |

## 安装

### 前置条件

- Hermes Agent Gateway 已安装并运行
- 有效的 MemOS API 密钥（[获取地址](https://memos-docs.openmem.net)）

### 安装步骤

```bash
# 克隆到 Hermes 插件目录
git clone https://github.com/ZacJinshare/hermes-memos-plugin.git ~/.hermes/plugins/memos
```

或手动将 `memos/` 文件夹复制到 `~/.hermes/plugins/memos/`。

### 配置

创建 `~/.hermes/memos.json`：

```json
{
  "api_key": "你的-memos-api-密钥",
  "base_url": "https://memos.memtensor.cn",
  "user_id": "hermes-user",
  "agent_id": "hermes"
}
```

或使用环境变量：

```bash
export MEMOS_API_KEY="你的-api-密钥"
export MEMOS_BASE_URL="https://memos.memtensor.cn"
export MEMOS_USER_ID="hermes-user"
export MEMOS_AGENT_ID="hermes"
```

### 在 Hermes 中启用

重启 Hermes 网关：

```bash
systemctl --user restart hermes-gateway
```

检查日志确认插件已加载：

```bash
tail -f ~/.hermes/logs/gateway.log | grep -i memos
```

## 使用方法

安装后，Hermes agent 将获得三个新工具：

### `memos_profile`

获取用户所有已存储记忆，建议在对话开始时调用。

### `memos_search`

按语义搜索记忆内容。

### `memos_conclude`

存储明确的事实（用户偏好、纠正、决策等）。

## 故障排查

**插件未加载：**
- 检查 `~/.hermes/plugins/memos/__init__.py` 是否存在
- 检查 `~/.hermes/logs/gateway.log` 中的导入错误
- 确认安装了 `requests`：`pip install requests`

**API 错误：**
- 连续失败 5 次后断路器触发，冷却 120 秒
- 查看 `/tmp/memos_plugin_debug.log` 获取详细调试输出
- 验证 `~/.hermes/memos.json` 中的 `api_key` 是否正确

## 开源协议

MIT License — 详见 [LICENSE](LICENSE)

## 相关链接

- [Hermes Agent](https://github.com/Hermes-ai/hermes)
- [MemOS 文档](https://memos-docs.openmem.net)
- [OpenMem API 参考](https://memos.memtensor.cn/docs)
