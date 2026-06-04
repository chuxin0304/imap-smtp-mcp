#!/usr/bin/env python3
import os
import json
import imaplib
import smtplib
import socket
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
import time
import logging

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("错误: 缺少 mcp 依赖库。请先运行 'pip install mcp'")
    exit(1)

# 设置全局网络超时时间（防止无响应卡死 LLM）
# 设置全局网络超时时间（防止无响应卡死 LLM）
socket.setdefaulttimeout(15)

mcp = FastMCP("Email Server")

def get_env_config():
    username = os.environ.get("EMAIL_USERNAME")
    password = os.environ.get("EMAIL_PASSWORD")
    imap_server = os.environ.get("IMAP_SERVER")
    smtp_server = os.environ.get("SMTP_SERVER")
    
    if not all([username, password, imap_server, smtp_server]):
        raise ValueError("缺少必要的环境变量配置。请确保在 MCP 客户端配置中设置了 EMAIL_USERNAME, EMAIL_PASSWORD, IMAP_SERVER 和 SMTP_SERVER。")
        
    return {
        "username": username,
        "password": password,
        "imap_server": imap_server,
        "smtp_server": smtp_server,
        "imap_port": int(os.environ.get("IMAP_PORT", 993)),
        "smtp_port": int(os.environ.get("SMTP_PORT", 465)),
    }

# -----------------
# 辅助函数: 解码与解析
# -----------------
def decode_str(s):
    if s is None:
        return ""
    value, charset = decode_header(s)[0]
    if charset:
        try:
            return value.decode(charset, errors='ignore')
        except Exception:
            return str(value)
    elif isinstance(value, bytes):
        try:
            return value.decode("utf-8", errors='ignore')
        except Exception:
            return str(value)
    else:
        return s

def strip_html(html_content):
    """剔除 HTML 标签，提取纯文本，节省 LLM Token"""
    if not html_content:
        return ""
    if BeautifulSoup:
        soup = BeautifulSoup(html_content, "html.parser")
        return soup.get_text(separator='\n', strip=True)
    else:
        import re
        text = re.sub(r'<style.*?>.*?</style>', '', html_content, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<[^>]+>', '\n', text)
        text = re.sub(r'\n\s*\n', '\n', text)
        return text.strip()

def get_email_body(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    charset = part.get_content_charset() or 'utf-8'
                    body = part.get_payload(decode=True).decode(charset, errors='ignore')
                    return body.strip() # 优先返回纯文本
                except Exception as e:
                    logging.warning(f"Error decoding plain text: {e}")
            elif content_type == "text/html" and "attachment" not in content_disposition and not body:
                try:
                    charset = part.get_content_charset() or 'utf-8'
                    html_body = part.get_payload(decode=True).decode(charset, errors='ignore')
                    body = strip_html(html_body)
                except Exception as e:
                    logging.warning(f"Error decoding html: {e}")
    else:
        try:
            charset = msg.get_content_charset() or 'utf-8'
            raw_body = msg.get_payload(decode=True).decode(charset, errors='ignore')
            if msg.get_content_type() == "text/html":
                body = strip_html(raw_body)
            else:
                body = raw_body
        except Exception as e:
            logging.warning(f"Error decoding body: {e}")
    return body.strip()

# 文件夹映射（适配常见的中文名称和 UTF-7 IMAP 编码）
FOLDER_MAP = {
    "收件箱": "INBOX",
    "草稿箱": "Drafts",
    "已发送": "Sent",
    "已删除": "Deleted Messages",
    "垃圾邮件": "Junk",
    "网易草稿箱": "&g0l6P3ux-",
    "网易已发送": "&bUuD7X-k-",
    "网易垃圾邮件": "&V4NXPp/D-",
    "网易已删除": "&XfJT0ZAB-"
}

def map_folder(folder_name):
    return FOLDER_MAP.get(folder_name, folder_name)

def handle_email_exception(e):
    if isinstance(e, imaplib.IMAP4.error):
        return {"error": f"IMAP 认证或操作失败: {str(e)}。请检查账号、密码/授权码及服务器地址。"}
    elif isinstance(e, smtplib.SMTPAuthenticationError):
        return {"error": f"SMTP 认证失败: {str(e)}。请检查账号和密码/授权码。"}
    elif isinstance(e, (socket.timeout, TimeoutError)):
        return {"error": "连接服务器超时。请检查网络或确认端口（如 993/465/587）是否受限。"}
    elif isinstance(e, ConnectionRefusedError):
        return {"error": "连接被拒绝。请检查服务器地址或端口配置。"}
    else:
         return {"error": f"发生意外错误: {str(e)}"}

# -----------------
# 工具 1: List Emails
# -----------------
@mcp.tool()
def list_emails(limit: int = 5, folder: str = "INBOX") -> str:
    """
    获取邮箱文件夹里的最新邮件列表（仅含标题、发件人等元信息，不含正文）。
    参数:
    - folder: 文件夹名称，支持 "INBOX", "收件箱", "已发送", "草稿箱" 等。
    - limit: 获取的邮件数量。
    """
    try:
        cfg = get_env_config()
        username = cfg['username']
        password = cfg['password']
        imap_server = cfg['imap_server']
        imap_port = cfg.get('imap_port', 993)

        folder_mapped = map_folder(folder)
        mail = imaplib.IMAP4_SSL(imap_server, imap_port)
        mail.login(username, password)
        
        status, response = mail.select(f'"{folder_mapped}"')
        if status != "OK":
            return json.dumps({"error": f"无法选择文件夹 '{folder}' (尝试映射为 '{folder_mapped}')。"}, ensure_ascii=False)
            
        status, messages = mail.search(None, "ALL")
        if status != "OK":
            return json.dumps({"error": "无法搜索邮件列表"}, ensure_ascii=False)
            
        email_ids = messages[0].split()
        if not email_ids:
             return json.dumps({"status": "success", "emails": [], "message": f"文件夹 '{folder}' 是空的"}, ensure_ascii=False)
             
        latest_email_ids = email_ids[-limit:]
        results = []
        
        for e_id in reversed(latest_email_ids):
            # 优化点：只拉取 HEADER 信息，不下载整个邮件内容
            status, msg_data = mail.fetch(e_id, "(BODY.PEEK[HEADER])")
            if status != "OK":
                continue
                
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    try:
                        msg = email.message_from_bytes(response_part[1])
                        subject = decode_str(msg.get("Subject", ""))
                        sender = decode_str(msg.get("From", ""))
                        date = decode_str(msg.get("Date", ""))
                        
                        results.append({
                            "id": e_id.decode(),
                            "subject": subject,
                            "from": sender,
                            "date": date
                        })
                    except Exception as parse_e:
                        logging.warning(f"Failed to parse email header {e_id}: {parse_e}")
                        
        mail.logout()
        return json.dumps({"status": "success", "emails": results}, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps(handle_email_exception(e), ensure_ascii=False)

# -----------------
# 工具 2: Read Email
# -----------------
@mcp.tool()
def read_email(email_id: str, folder: str = "INBOX") -> str:
    """
    根据 list_emails 提供的 email_id，读取该封邮件的完整正文内容。
    """
    try:
        cfg = get_env_config()
        username = cfg['username']
        password = cfg['password']
        imap_server = cfg['imap_server']
        imap_port = cfg.get('imap_port', 993)

        folder_mapped = map_folder(folder)
        mail = imaplib.IMAP4_SSL(imap_server, imap_port)
        mail.login(username, password)
        mail.select(f'"{folder_mapped}"')
        
        status, msg_data = mail.fetch(email_id.encode(), "(RFC822)")
        if status != "OK" or not msg_data or msg_data[0] is None:
            return json.dumps({"error": f"无法获取 ID 为 {email_id} 的邮件。"}, ensure_ascii=False)
            
        response_part = msg_data[0]
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])
            subject = decode_str(msg.get("Subject", ""))
            sender = decode_str(msg.get("From", ""))
            date = decode_str(msg.get("Date", ""))
            body = get_email_body(msg)
            
            mail.logout()
            return json.dumps({
                "status": "success",
                "email": {
                    "id": email_id,
                    "subject": subject,
                    "from": sender,
                    "date": date,
                    "body": body
                }
            }, ensure_ascii=False, indent=2)
            
        mail.logout()
        return json.dumps({"error": "解析邮件失败。"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps(handle_email_exception(e), ensure_ascii=False)

# -----------------
# 工具 3: Send Email
# -----------------
@mcp.tool()
def send_email(to_addrs: str, subject: str, body: str) -> str:
    """
    通过邮箱发送一封纯文本邮件。
    参数:
    - to_addrs: 收件人邮箱，支持多个用逗号分隔。
    """
    try:
        cfg = get_env_config()
        username = cfg['username']
        password = cfg['password']
        smtp_server = cfg['smtp_server']
        smtp_port = cfg.get('smtp_port', 465)

        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = to_addrs
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        if smtp_port in [587, 25]:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            
        server.login(username, password)
        
        recipients = [e.strip() for e in to_addrs.split(',') if e.strip()]
        server.send_message(msg, from_addr=username, to_addrs=recipients)
        server.quit()
        
        return json.dumps({
            "status": "success", 
            "message": "邮件发送成功",
            "to": recipients,
            "subject": subject
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps(handle_email_exception(e), ensure_ascii=False)

# -----------------
# 工具 4: Save Draft
# -----------------
@mcp.tool()
def save_draft(subject: str, body: str, to_addrs: str = "") -> str:
    """
    将一封草稿邮件静默保存到邮箱的草稿箱文件夹中。
    """
    try:
        cfg = get_env_config()
        username = cfg['username']
        password = cfg['password']
        imap_server = cfg['imap_server']
        imap_port = cfg.get('imap_port', 993)

        msg = MIMEMultipart()
        msg['From'] = username
        if to_addrs:
            msg['To'] = to_addrs
        msg['Subject'] = subject
        msg['Date'] = formatdate(localtime=True)
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        mail = imaplib.IMAP4_SSL(imap_server, imap_port)
        mail.login(username, password)
        
        msg_bytes = msg.as_bytes()
        internal_date = imaplib.Time2Internaldate(time.time())
        
        draft_folders = ['"Drafts"', '"&g0l6P3ux-"', '"草稿箱"', '"INBOX.Drafts"']
        success = False
        error_msg = ""
        
        for f in draft_folders:
            status, response = mail.append(f, '(\\Draft)', internal_date, msg_bytes)
            if status == 'OK':
                success = True
                break
            else:
                error_msg = response

        mail.logout()
        
        if success:
            return json.dumps({
                "status": "success", 
                "message": "邮件已成功保存到草稿箱",
                "subject": subject
            }, ensure_ascii=False, indent=2)
        else:
            return json.dumps({"error": f"无法存入草稿箱: {error_msg}"}, ensure_ascii=False)
            
    except Exception as e:
        return json.dumps(handle_email_exception(e), ensure_ascii=False)

if __name__ == "__main__":
    mcp.run()
