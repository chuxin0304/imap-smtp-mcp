#!/usr/bin/env python3
import os
import json
import imaplib
import smtplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
import time
import logging

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("错误: 缺少 mcp 依赖库。请先运行 'pip install mcp'")
    exit(1)

mcp = FastMCP("126 Email Server")

def get_config():
    """读取配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if not os.path.exists(config_path):
        raise Exception(f"配置文件不存在: {config_path}")
        
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
        
    username = config.get("email_address")
    password = config.get("auth_code")
    
    if not username or not password or username == "your_email@example.com":
        raise Exception("未配置有效的邮箱账号或授权码，请检查 config.json")
        
    return config

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
                    break
                except Exception as e:
                    logging.warning(f"Error decoding plain text: {e}")
            elif content_type == "text/html" and "attachment" not in content_disposition and not body:
                try:
                    charset = part.get_content_charset() or 'utf-8'
                    body = part.get_payload(decode=True).decode(charset, errors='ignore')
                except Exception as e:
                    logging.warning(f"Error decoding html: {e}")
    else:
        try:
            charset = msg.get_content_charset() or 'utf-8'
            body = msg.get_payload(decode=True).decode(charset, errors='ignore')
        except Exception as e:
            logging.warning(f"Error decoding body: {e}")
    return body.strip()

# -----------------
# 工具 1: Fetch Emails
# -----------------
@mcp.tool()
def fetch_emails(limit: int = 5) -> str:
    """获取企业邮箱收件箱里的最新邮件列表"""
    try:
        config = get_config()
        username = config["email_address"]
        password = config["auth_code"]
        imap_server = config.get("imap_server")
        if not imap_server:
            return json.dumps({"error": "未配置 imap_server"}, ensure_ascii=False)
        folder = config.get("folder", "inbox")

        mail = imaplib.IMAP4_SSL(imap_server, 993)
        mail.login(username, password)
        mail.select(f'"{folder}"')
        
        status, messages = mail.search(None, "ALL")
        if status != "OK":
            return json.dumps({"error": "无法获取邮件列表"}, ensure_ascii=False)
            
        email_ids = messages[0].split()
        if not email_ids:
             return json.dumps({"status": "success", "emails": [], "message": "邮箱是空的"}, ensure_ascii=False)
             
        latest_email_ids = email_ids[-limit:]
        results = []
        
        for e_id in reversed(latest_email_ids):
            status, msg_data = mail.fetch(e_id, "(RFC822)")
            if status != "OK":
                continue
                
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    try:
                        msg = email.message_from_bytes(response_part[1])
                        subject = decode_str(msg.get("Subject", ""))
                        sender = decode_str(msg.get("From", ""))
                        date = decode_str(msg.get("Date", ""))
                        body = get_email_body(msg)
                        
                        results.append({
                            "id": e_id.decode(),
                            "subject": subject,
                            "from": sender,
                            "date": date,
                            "body": body[:1000] + ("..." if len(body) > 1000 else "")
                        })
                    except Exception as parse_e:
                        logging.warning(f"Failed to parse email {e_id}: {parse_e}")
                        
        mail.logout()
        return json.dumps({"status": "success", "emails": results}, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

# -----------------
# 工具 2: Send Email
# -----------------
@mcp.tool()
def send_email(to_addrs: str, subject: str, body: str) -> str:
    """通过企业邮箱发送一封纯文本邮件。参数 to_addrs 支持多个邮箱用逗号分隔。"""
    try:
        config = get_config()
        username = config["email_address"]
        password = config["auth_code"]
        smtp_server = config.get("smtp_server")
        if not smtp_server:
            return json.dumps({"error": "未配置 smtp_server"}, ensure_ascii=False)

        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = to_addrs
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        server = smtplib.SMTP_SSL(smtp_server, 465)
        server.login(username, password)
        
        recipients = [email.strip() for email in to_addrs.split(',')]
        server.send_message(msg, from_addr=username, to_addrs=recipients)
        server.quit()
        
        return json.dumps({
            "status": "success", 
            "message": "邮件发送成功",
            "to": recipients,
            "subject": subject
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

# -----------------
# 工具 3: Save Draft
# -----------------
@mcp.tool()
def save_draft(subject: str, body: str, to_addrs: str = "") -> str:
    """将一封草稿邮件静默保存到企业邮箱的草稿箱文件夹中。"""
    try:
        config = get_config()
        username = config["email_address"]
        password = config["auth_code"]
        imap_server = config.get("imap_server")
        if not imap_server:
            return json.dumps({"error": "未配置 imap_server"}, ensure_ascii=False)

        msg = MIMEMultipart()
        msg['From'] = username
        if to_addrs:
            msg['To'] = to_addrs
        msg['Subject'] = subject
        msg['Date'] = formatdate(localtime=True)
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        mail = imaplib.IMAP4_SSL(imap_server, 993)
        mail.login(username, password)
        
        msg_bytes = msg.as_bytes()
        internal_date = imaplib.Time2Internaldate(time.time())
        
        # 尝试英文和中文的草稿箱命名
        status, response = mail.append("Drafts", '(\\Draft)', internal_date, msg_bytes)
        if status != 'OK':
            status, response = mail.append("&g0l6P3ux-", '(\\Draft)', internal_date, msg_bytes)
            if status != 'OK':
                raise Exception(f"Failed to append to draft folder: {response}")

        mail.logout()
        
        return json.dumps({
            "status": "success", 
            "message": "邮件已成功保存到草稿箱",
            "subject": subject
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

if __name__ == "__main__":
    mcp.run()