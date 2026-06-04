# 邮箱管理工具 (IMAP/SMTP Email Skill)

## 技能说明
本技能用于连接用户的邮箱服务器并进行邮件管理（支持所有标准的 IMAP/SMTP 协议），它既可以通过命令行脚本运行，也被封装成了标准的 MCP 服务器。
支持以下功能：
1. **获取邮件**：获取最新邮件列表，支持指定读取的邮件数量及文件夹名称。
2. **发送邮件**：通过 SMTP 发送简单纯文本邮件。
3. **保存草稿**：通过 IMAP 保存邮件到草稿箱。

所有鉴权信息（账号、密码/授权码、服务器地址）均通过参数直接传入，不依赖本地配置文件，更加安全灵活。

## 使用说明 (命令行脚本)

### 1. 接收邮件
```bash
python3 ~/.agents/skills/fetch-126-email/scripts/fetch_emails.py --username "your@email.com" --password "auth_code" --imap_server "imap.example.com" --limit 5
```

### 2. 发送邮件
```bash
python3 ~/.agents/skills/fetch-126-email/scripts/send_email.py --username "your@email.com" --password "auth_code" --smtp_server "smtp.example.com" --to "user@example.com" --subject "主题" --body "正文"
```

### 3. 保存邮件草稿
```bash
python3 ~/.agents/skills/fetch-126-email/scripts/save_draft.py --username "your@email.com" --password "auth_code" --imap_server "imap.example.com" --to "user@example.com" --subject "主题" --body "正文"
```

### 4. 使用标准英文邮件模板 (Templates)
我们在 `templates.json` 中内置了一些标准的英文商务邮件模板（包含会议邀请、跟进、进度汇报、感谢信等）。
当用户希望“发一封标准英文邮件”或“使用某某模板发送邮件”时：
1. 你可以先读取 `~/.agents/skills/fetch-126-email/templates.json` 获取对应的模板结构。
2. 智能填充模板中的占位符（如 `{name}`, `{topic}`, `{sender_name}` 等）。
3. 使用拼接好之后的英文内容发送邮件或存为草稿。

## 使用说明 (MCP Server)
本技能包含一个标准的 FastMCP 服务端 `server.py`。
安装依赖：`pip install mcp`
注册为 MCP 时，Command 填写 `python3`，Args 填写 `~/.agents/skills/fetch-126-email/server.py`。
启动后，所有 LLM 都可以直接调用 `fetch_emails`, `send_email`, `save_draft` 工具，直接通过参数传入认证信息即可使用。
