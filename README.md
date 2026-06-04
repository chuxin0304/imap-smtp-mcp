# IMAP/SMTP Email MCP Server

## 简介
这是一个标准的 Model Context Protocol (MCP) 服务器，用于连接用户的邮箱并进行邮件管理。支持所有标准的 IMAP/SMTP 协议。

提供了以下核心 MCP Tools 供 LLM 调用：
1. **`list_emails`**: 快速获取邮件列表元数据（发件人、标题、日期等），极大减少不必要的流量消耗。
2. **`read_email`**: 根据邮件 ID 提取指定邮件的完整正文，内置 HTML 解析和标签剔除功能，有效避免 Token 超限。
3. **`send_email`**: 通过 SMTP 发送简单纯文本邮件（自动适配 465/SSL 和 587/STARTTLS 端口）。
4. **`save_draft`**: 通过 IMAP 保存邮件到草稿箱，内置常见中英文草稿箱文件夹的自动适配。

*注：所有鉴权信息（账号、密码/授权码、服务器地址）均由 LLM 在调用 Tool 时通过参数传入，无需本地配置文件，确保数据安全。*

## 项目结构
本仓库符合标准的 Python MCP 项目规范：
- `server.py`：MCP 服务器的主入口逻辑。
- `pyproject.toml` / `requirements.txt`：项目依赖管理配置。

## 快速运行与使用

### 1. 安装依赖
```bash
pip install -r requirements.txt
# 或者
pip install .
```

### 2. 在支持 MCP 的客户端中配置

#### 选项 A：Claude Desktop 配置文件模板
如果你使用的是 Claude Desktop，请打开或创建配置文件（通常位于 `~/Library/Application Support/Claude/claude_desktop_config.json` 或 `%APPDATA%\Claude\claude_desktop_config.json`），添加以下内容：

```json
{
  "mcpServers": {
    "email-server": {
      "command": "python3",
      "args": [
        "/Users/你的用户名/Code/imap-smtp-mcp/server.py"
      ]
    }
  }
}
```
*(注：Windows 用户请使用如 `C:\\Code\\imap-smtp-mcp\\server.py` 的绝对路径。如果你使用了虚拟环境，也可将 `"command"` 修改为该虚拟环境内 `python` 执行文件的绝对路径。)*

#### 选项 B：其他图形化客户端（如 Enchanté 等）
在添加 MCP Server 的界面中填入：
- **Name**: `Email Server` (或任意自定义名称)
- **Command**: `python3` (或虚拟环境中 python 的绝对路径)
- **Args**: `/Users/你的用户名/Code/imap-smtp-mcp/server.py`

### 3. AI 对话 / Prompt 使用示例（必看 🌟）

本项目为了保障最高级别的隐私与安全，**未在本地保留任何账号配置文件**（无状态设计）。所有的登录与连接信息均由 LLM 动态传入。

因此，为了让 AI 助手成功连接到你的邮箱，你需要**在对话框里，将邮箱的基础配置信息通过自然语言直接告诉它**。

**👉 你可以直接复制以下 Prompt 模板发给 AI：**
> "你现在是我的私人邮件管家，请使用以下配置信息帮我处理邮件：
> - 邮箱账号：your_email@example.com
> - 授权码/密码：your_app_password
> - IMAP 服务器：imap.example.com
> - SMTP 服务器：smtp.example.com
> 
> 现在，请帮我检查一下「收件箱」里今天最新的 3 封邮件，并用中文帮我总结。如果没有新邮件，请帮我起草一封致谢信存入「草稿箱」。"

*💡 安全建议：强烈推荐在各大邮箱提供商（如 QQ邮箱、网易邮箱、Gmail、Outlook 等）的账户设置中，生成并使用**第三方应用授权码**来代替你的主登录密码。*

---
配置完成并发送上述提示词后，LLM 即可自动感知并调用上述四个工具进行顺畅的收发邮件操作！
