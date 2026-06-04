# IMAP/SMTP Email MCP Server

## 简介
这是一个标准的 Model Context Protocol (MCP) 服务器，用于连接用户的邮箱并进行邮件管理。支持所有标准的 IMAP/SMTP 协议。

提供了以下核心 MCP Tools 供 LLM 调用：
1. **`list_emails`**: 快速获取邮件列表元数据（发件人、标题、日期等），极大减少不必要的流量消耗。
2. **`read_email`**: 根据邮件 ID 提取指定邮件的完整正文，内置 HTML 解析和标签剔除功能，有效避免 Token 超限。
3. **`send_email`**: 通过 SMTP 发送简单纯文本邮件（自动适配 465/SSL 和 587/STARTTLS 端口）。
4. **`save_draft`**: 通过 IMAP 保存邮件到草稿箱，内置常见中英文草稿箱文件夹的自动适配。

*注：为了隐私与安全，账号配置信息将存储在本地的 `config.json` 中，LLM 仅需传入操作指令，无需知道你的邮箱密码。*

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

### 2. 本地账号配置（必看 🌟）

在项目根目录下创建一个名为 `config.json` 的文件，将你的邮箱配置填入其中（请注意不要将此文件提交到公开的 Git 仓库）。

**👉 `config.json` 配置模板：**
```json
{
  "username": "your_email@example.com",
  "password": "your_app_password",
  "imap_server": "imap.example.com",
  "smtp_server": "smtp.example.com",
  "imap_port": 993,
  "smtp_port": 465
}
```
*💡 安全建议：强烈推荐在各大邮箱提供商（如 QQ邮箱、网易邮箱、Gmail、Outlook 等）的账户设置中，生成并使用**第三方应用授权码**来代替你的主登录密码。*

### 3. 在支持 MCP 的客户端中配置

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

### 4. 运行与使用
配置完成并在客户端加载该 MCP Server 后，你可以直接通过自然语言对 AI 助手说：
> "帮我检查一下收件箱有没有新邮件"
> "写一封邮件给 xxx@example.com，告诉他我明天开会，直接发送"
