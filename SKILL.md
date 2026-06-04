---
name: fetch-126-email
description: 获取和发送支持 IMAP/SMTP 协议的邮箱邮件，支持通过 IMAP 协议读取指定文件夹，以及通过 SMTP 发送邮件。配置文件保存在 config.json 中。
---

# 获取 126 / 网易企业邮箱邮件 (fetch-126-email)

## 技能说明
本技能用于连接用户的邮箱服务器并进行邮件管理（支持所有标准的 IMAP/SMTP 协议）：
1. **获取邮件**：获取最新邮件列表，支持指定读取的邮件数量及文件夹名称。
2. **发送邮件**：通过 SMTP 发送简单纯文本邮件。

安全起见，用户的密码/授权码等配置信息保存在该目录下的 `config.json` 文件中。

## 首次使用前配置
用户需要前往 `~/.agents/skills/fetch-126-email/config.json` 文件中，手动填入以下信息：
```json
{
  "email_address": "your_email@example.com",
  "auth_code": "你的IMAP授权码或客户端密码",
  "imap_server": "imap.example.com",
  "smtp_server": "smtp.example.com",
  "folder": "inbox"
}
```
**注意：** 
* `imap_server` 和 `smtp_server` **必填**，请填写你所使用邮箱服务商提供的服务器地址（如：163邮箱对应 `imap.163.com` / `smtp.163.com`，QQ邮箱对应 `imap.qq.com` / `smtp.qq.com`）。
* `folder` 代表读取的目标文件夹，默认为 `"inbox"`（收件箱）。若要读取其他文件夹可在此修改（如：`"Sent"`，`"Drafts"` 等）。

## 使用说明

### 1. 接收邮件
当用户要求查询其企业邮箱的邮件时，你可以调用此技能提供的脚本。
执行该脚本，请务必使用 `native-tools___bash` 工具运行以下命令：

```bash
python3 ~/.agents/skills/fetch-126-email/scripts/fetch_emails.py [limit]
```

参数说明：
- `[limit]`: 可选参数，获取最新邮件的数量，默认为 5 封。

### 2. 发送邮件
当用户要求发送邮件时，调用发送脚本：

```bash
python3 ~/.agents/skills/fetch-126-email/scripts/send_email.py --to "user@example.com" --subject "主题" --body "正文内容"
```

参数说明：
- `--to`: 必填，收件人邮箱地址（如果给多人发送，用逗号 `,` 分隔）。
- `--subject`: 必填，邮件的主题。
- `--body`: 必填，邮件正文内容。

### 3. 保存邮件草稿
当用户要求起草、写一封邮件并保存到草稿箱时，调用保存草稿脚本：

```bash
python3 ~/.agents/skills/fetch-126-email/scripts/save_draft.py --to "user@example.com" --subject "主题" --body "正文内容"
```

参数说明：
- `--to`: 可选，收件人邮箱地址（如果暂时不确定收件人可以省略此参数）。
- `--subject`: 必填，邮件的主题。
- `--body`: 必填，邮件正文内容。

### 4. 使用标准英文邮件模板 (Templates)
我们在 `templates.json` 中内置了一些标准的英文商务邮件模板（包含会议邀请、跟进、进度汇报、感谢信等）。
当用户希望“发一封标准英文邮件”或“使用某某模板发送邮件”时：
1. 你可以先读取 `~/.agents/skills/fetch-126-email/templates.json` 获取对应的模板结构。
2. 使用用户的上下文及要求，智能填充模板中的占位符（如 `{name}`, `{topic}`, `{sender_name}` 等）。
3. 使用拼接好之后的英文内容，调用 `send_email.py` 为用户发送邮件。

## 获取授权码说明
如果遇到无法登录的情况，请确保：
1. 网页端已经开启了 IMAP/SMTP 服务。
2. 企业邮箱如果开启了安全验证，可能需要生成专用的**客户端授权码**代替常规登录密码。