# hermes-memos-plugin

[English](#english) | [中文](#中文)

---

<a name="english"></a>
# Hermes MemOS Plugin

[![GitHub license](https://img.shields.io/github/license/ZacLou/hermes-memos-plugin)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/ZacLou/hermes-memos-plugin)](https://github.com/ZacLou/hermes-memos-plugin/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/ZacLou/hermes-memos-plugin)](https://github.com/ZacLou/hermes-memos-plugin/network)

A **memory provider plugin** for [Hermes AI Agent](https://github.com/Hermes-ai/hermes) that integrates [MemOS OpenMem API](https://memos-docs.openmem.net) to give your agent **persistent, cross-session memory**.

> Give your Hermes agent the ability to remember who the user is, what they like, and what you've discussed — just like a real assistant.

## ✨ Features

- 🧠 **Persistent Memory** — Facts survive across conversations and restarts
- 🔍 **Semantic Search** — Retrieve memories by *meaning*, not keywords
- 🔄 **Auto Sync** — Background thread stores conversations without blocking
- 🛡️ **Circuit Breaker** — Graceful degradation when MemOS API is down
- ⚡ **Zero Config** — Works with just an API key
- 🎯 **Karpathy-Style Code** — Minimal, readable, ~240 lines

## 🛠️ Tools Provided

| Tool | Description |
|------|-------------|
| `memos_profile` | Load all stored memories (call at conversation start) |
| `memos_search` | Semantic search over stored memories |
| `memos_conclude` | Store a specific fact about the user |

## 📦 Installation

### Prerequisites

- [Hermes Agent Gateway](https://github.com/Hermes-ai/hermes) installed and running
- A [MemOS API key](https://memos-docs.openmem.net)

### Install

```bash
# Clone to Hermes plugins directory
git clone https://github.com/ZacLou/hermes-memos-plugin.git ~/.hermes/plugins/memos
```

Or manually copy `memos/` to `~/.hermes/plugins/memos/`.

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

### Enable

Restart Hermes:

```bash
systemctl --user restart hermes-gateway
```

Verify it loaded:

```bash
grep -i memos ~/.hermes/logs/gateway.log
```

## 🚀 Usage

Once installed, Hermes automatically gains three new tools:

### `memos_profile`

> **When to use:** At the start of a conversation, to load user context.

```
User: "Hi there!"
Agent: [calls memos_profile]
        "Welcome back! I see you prefer Python over JavaScript. Let's continue."
```

### `memos_search`

> **When to use:** When you need to recall something the user mentioned before.

```
Agent: [calls memos_search with query "user's preferred code style"]
```

### `memos_conclude`

> **When to use:** When the user states a preference, correction, or decision.

```
User: "Actually, I prefer single quotes in Python."
Agent: [calls memos_conclude with conclusion "User prefers single quotes in Python"]
```

## 🔌 API Endpoints Used

| Endpoint | Method | Purpose |
|----------|---------|---------|
| `/api/openmem/v1/add/message` | POST | Store conversation messages |
| `/api/openmem/v1/search/memory` | POST | Semantic search over memories |
| `/api/openmem/v1/get/memory` | POST | Retrieve all stored memories |

## 🐛 Troubleshooting

**Plugin not loading:**
- Check `~/.hermes/plugins/memos/__init__.py` exists
- Check `~/.hermes/logs/gateway.log` for import errors
- Verify `requests` is installed: `pip install requests`

**API errors / circuit breaker tripped:**
- Circuit breaker trips after 5 consecutive failures, cools down for 120s
- Check MemOS API key in `~/.hermes/memos.json`
- Test API manually: `curl -H "Authorization: Token YOUR_KEY" https://memos.memtensor.cn/api/openmem/v1/get/memory -d '{"user_id":"test","page":1,"size":1}' -X POST -H "Content-Type: application/json"`

## 🤝 Contributing

PRs welcome! Please:

1. Follow the [Karpathy Coding Guidelines](https://github.com/ZacLou/hermes-memos-plugin/blob/main/docs/karpathy-guidelines.md)
2. Keep it simple — no over-engineering
3. Test with a running Hermes instance before submitting

## 📄 License

MIT — see [LICENSE](LICENSE)

## 🔗 Links

- [Hermes Agent](https://github.com/Hermes-ai/hermes)
- [MemOS Documentation](https://memos-docs.openmem.net)
- [OpenMem API](https://memos.memtensor.cn/docs)

---

<a name="中文"></a>
# Hermes MemOS 插件

[![GitHub license](https://img.shields.io/github/license/ZacLou/hermes-memos-plugin)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/ZacLou/hermes-memos-plugin)](https://github.com/ZacLou/hermes-memos-plugin/stargazers)

为 [Hermes AI Agent](https://github.com/Hermes-ai/hermes) 开发的**记忆提供者插件**，集成 [MemOS OpenMem API](https://memos-docs.openmem.net)，赋予你的 Agent **持久化、跨会话的记忆能力**。

> 让你的 Hermes agent 能够记住用户是谁、喜欢什么、讨论过什么 —— 就像真正的助手一样。

## ✨ 功能特性

- 🧠 **持久化记忆** — 事实存储跨对话、跨重启保留
- 🔍 **语义搜索** — 按*语义*检索记忆，而非关键词
- 🔄 **自动同步** — 后台线程无阻塞存储对话
- 🛡️ **断路器保护** — MemOS API 宕机时优雅降级
- ⚡ **零配置启动** — 只需 API 密钥
- 🎯 **Karpathy 风格代码** — 简洁、可读、约 240 行

## 🛠️ 提供的工具

| 工具 | 说明 |
|------|------|
| `memos_profile` | 加载所有已存储记忆（对话开始时调用） |
| `memos_search` | 对存储的记忆进行语义搜索 |
| `memos_conclude` | 存储关于用户的特定事实 |

## 📦 安装

### 前置条件

- [Hermes Agent Gateway](https://github.com/Hermes-ai/hermes) 已安装并运行
- 有效的 [MemOS API 密钥](https://memos-docs.openmem.net)

### 安装步骤

```bash
# 克隆到 Hermes 插件目录
git clone https://github.com/ZacLou/hermes-memos-plugin.git ~/.hermes/plugins/memos
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

### 启用

重启 Hermes：

```bash
systemctl --user restart hermes-gateway
```

验证插件已加载：

```bash
grep -i memos ~/.hermes/logs/gateway.log
```

## 🚀 使用方法

安装后，Hermes 自动获得三个新工具：

### `memos_profile`

> **使用时机：** 对话开始时，加载用户上下文。

### `memos_search`

> **使用时机：** 需要回忆用户之前提到过的内容时。

### `memos_conclude`

> **使用时机：** 用户陈述偏好、纠正或决策时。

## 🔌 使用的 API 端点

| 端点 | 方法 | 用途 |
|------|------|------|
| `/api/openmem/v1/add/message` | POST | 存储对话消息 |
| `/api/openmem/v1/search/memory` | POST | 语义搜索记忆 |
| `/api/openmem/v1/get/memory` | POST | 检索所有已存储记忆 |

## 🐛 故障排查

**插件未加载：**
- 检查 `~/.hermes/plugins/memos/__init__.py` 是否存在
- 检查 `~/.hermes/logs/gateway.log` 中的导入错误
- 确认安装了 `requests`：`pip install requests`

**API 错误 / 断路器触发：**
- 连续失败 5 次后断路器触发，冷却 120 秒
- 检查 `~/.hermes/memos.json` 中的 MemOS API 密钥
- 手动测试 API（见英文版）

## 🤝 贡献

欢迎 PR！请：

1. 遵循 [Karpathy 编码准则](https://github.com/ZacLou/hermes-memos-plugin/blob/main/docs/karpathy-guidelines.md)
2. 保持简洁 — 不要过度工程化
3. 提交前在运行的 Hermes 实例中测试

## 📄 开源协议

MIT License — 详见 [LICENSE](LICENSE)

## 🔗 相关链接

- [Hermes Agent](https://github.com/Hermes-ai/hermes)
- [MemOS 文档](https://memos-docs.openmem.net)
- [OpenMem API](https://memos.memtensor.cn/docs)
