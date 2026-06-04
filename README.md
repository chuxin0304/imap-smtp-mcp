# IMAP/SMTP Email MCP Server

## 简介
这是一个标准的 Model Context Protocol (MCP) 服务器，用于连接用户的邮箱并进行邮件管理。支持所有标准的 IMAP/SMTP 协议。

提供了以下核心 MCP Tools 供 LLM 调用：
1. **`fetch_emails`**: 获取最新邮件列表，支持指定读取的邮件数量及文件夹名称。
2. **`send_email`**: 通过 SMTP 发送简单纯文本邮件。
3. **`save_draft`**: 通过 IMAP 保存邮件到草稿箱。

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

启动后，LLM 即可自动感知并调用上述三个工具进行收发邮件。
