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

### 2. 在支持 MCP 的客户端（如 Enchanté, Claude Desktop）中配置
- **Name**: `Email Server` (或任意名称)
- **Command**: `python3`
- **Args**: `[此处填写你的绝对路径]/server.py`

启动后，LLM 即可自动感知并调用上述四个工具进行收发邮件。
