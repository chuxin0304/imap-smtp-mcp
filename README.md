# IMAP/SMTP Email MCP Server

## 简介
这是一个标准的 Model Context Protocol (MCP) 服务器，用于连接用户的邮箱并进行邮件管理。支持所有标准的 IMAP/SMTP 协议。

提供了以下核心 MCP Tools 供 LLM 调用：
1. **`list_emails`**: 快速获取邮件列表元数据（发件人、标题、日期等），极大减少不必要的流量消耗。
2. **`read_email`**: 根据邮件 ID 提取指定邮件的完整正文，内置 HTML 解析和标签剔除功能，有效避免 Token 超限。
3. **`send_email`**: 通过 SMTP 发送简单纯文本邮件（自动适配 465/SSL 和 587/STARTTLS 端口）。
4. **`save_draft`**: 通过 IMAP 保存邮件到草稿箱，内置常见中英文草稿箱文件夹的自动适配。

*注：为了隐私与安全，账号配置信息通过 MCP 客户端的环境变量 (`env`) 注入，代码完全解耦且无状态，LLM 仅需调用极简的工具指令即可，无需接触密码。*

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

### 2. 在支持 MCP 的客户端中配置（通过环境变量传入账号配置）

对于无状态的 MCP Server，使用 **环境变量 (Environment Variables)** 注入鉴权信息是最标准、最安全的做法。

#### 选项 A：Claude Desktop 配置文件模板
请打开或创建配置文件（通常位于 `~/Library/Application Support/Claude/claude_desktop_config.json` 或 `%APPDATA%\Claude\claude_desktop_config.json`），添加以下内容（注意其中的 `env` 字段）：

```json
{
  "mcpServers": {
    "email-server": {
      "command": "python3",
      "args": [
        "/Users/你的用户名/Code/imap-smtp-mcp/server.py"
      ],
      "env": {
        "EMAIL_USERNAME": "your_email@qiye.163.com",
        "EMAIL_PASSWORD": "your_client_auth_code",
        "IMAP_SERVER": "imap.qiye.163.com",
        "SMTP_SERVER": "smtp.qiye.163.com",
        "IMAP_PORT": "993",
        "SMTP_PORT": "465"
      }
    }
  }
}
```
*(注：Windows 用户请使用绝对路径，如 `C:\\Code\\imap-smtp-mcp\\server.py`。强烈建议在各大邮箱提供商中生成并使用**第三方应用授权码**代替主密码。)*

#### 选项 B：其他图形化客户端（如 Enchanté 等）
在添加 MCP Server 的配置界面中，除了填写路径，请务必找到 **Environment Variables / Env** 区域，并添加以下键值对：
- `EMAIL_USERNAME`: your_email@qiye.163.com (你的网易企业邮箱账号)
- `EMAIL_PASSWORD`: your_client_auth_code (客户端授权密码)
- `IMAP_SERVER`: imap.qiye.163.com
- `SMTP_SERVER`: smtp.qiye.163.com
- `IMAP_PORT`: 993 *(选填，网易企业邮箱默认的 SSL/TLS 端口即为 993)*
- `SMTP_PORT`: 465 *(选填，网易企业邮箱默认的 SSL/TLS 端口即为 465)*

### 3. 运行与使用
配置完成并重启你的 MCP 客户端后，即可直接使用自然语言对 AI 助手下发指令，不需要告诉它任何密码或配置信息：
> "帮我检查一下收件箱今天有没有重要的新邮件"
> "请帮我起草一封给 xxx@example.com 的会议纪要并保存到草稿箱"
