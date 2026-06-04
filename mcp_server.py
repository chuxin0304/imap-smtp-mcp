# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "mcp",
# ]
# ///

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

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("fetch-126-email", description="网易/126邮箱邮件收发工具")

def get_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def check_config():
    config = get_config()
    username = config.get("email_address")
    password = config.get("auth_code")
    if not username or not password or username == "your_email@your_company_domain.com":
        raise ValueError("邮箱账号未正确配置，请检查 config.json。")
    return config

@mcp.tool()
def send_email(to_addrs: str, subject: str, body: str) -> str:
    """发送一封纯文本邮件。"""
    config = check_config()
    username = config["email_address"]
    password = config["auth_code"]
    smtp_server = config.get("smtp_server", "smtp.qiye.163.com")
    
    msg = MIMEMultipart()
    msg['From'] = username
    msg['To'] = to_addrs
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP_SSL(smtp_server, 465)
        server.login(username, password)
        recipients = [email.strip() for email in to_addrs.split(',')]
        server.send_message(msg, from_addr=username, to_addrs=recipients)
        server.quit()
        return f"成功：邮件已发送给 {to_addrs}，主题：{subject}"
    except Exception as e:
        return f"发送失败：{str(e)}"

@mcp.tool()
def save_draft(subject: str, body: str, to_addrs: str = "") -> str:
    """将草稿邮件保存到邮箱的草稿箱 (Drafts)。"""
    config = check_config()
    username = config["email_address"]
    password = config["auth_code"]
    imap_server = config.get("imap_server", "imap.qiye.163.com")
    
    msg = MIMEMultipart()
    msg['From'] = username
    if to_addrs:
        msg['To'] = to_addrs
    msg['Subject'] = subject
    msg['Date'] = formatdate(localtime=True)
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        mail = imaplib.IMAP4_SSL(imap_server, 993)
        mail.login(username, password)
        msg_bytes = msg.as_bytes()
        internal_date = imaplib.Time2Internaldate(time.time())
        
        status, response = mail.append("Drafts", '(\\Draft)', internal_date, msg_bytes)
        if status != 'OK':
            status, response = mail.append("&g0l6P3ux-", '(\\Draft)', internal_date, msg_bytes)
            if status != 'OK':
                return f"草稿保存失败，文件夹不存在：{response}"

        mail.logout()
        return f"成功：草稿已保存，主题：{subject}"
    except Exception as e:
        return f"草稿保存发生错误：{str(e)}"

def decode_str(s):
    if s is None:
        return ""
    value, charset = decode_header(s)[0]
    if charset:
        try:
            return value.decode(charset, errors='ignore')
        except:
            return str(value)
    elif isinstance(value, bytes):
        try:
            return value.decode("utf-8", errors='ignore')
        except:
            return str(value)
    return s

def get_email_body(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdisp = str(part.get("Content-Disposition"))
            if ctype == "text/plain" and "attachment" not in cdisp:
                charset = part.get_content_charset() or 'utf-8'
                body = part.get_payload(decode=True).decode(charset, errors='ignore')
                break
    else:
        charset = msg.get_content_charset() or 'utf-8'
        body = msg.get_payload(decode=True).decode(charset, errors='ignore')
    return body.strip()

@mcp.tool()
def fetch_emails(limit: int = 5) -> str:
    """从收件箱获取最近的 N 封邮件（默认 5 封）。"""
    config = check_config()
    username = config["email_address"]
    password = config["auth_code"]
    imap_server = config.get("imap_server", "imap.qiye.163.com")
    folder = config.get("folder", "inbox")
    
    try:
        mail = imaplib.IMAP4_SSL(imap_server, 993)
        mail.login(username, password)
        mail.select(f'"{folder}"')
        status, messages = mail.search(None, "ALL")
        if status != "OK":
            return "无法获取邮件列表"
            
        email_ids = messages[0].split()
        if not email_ids:
            return "邮箱是空的"
            
        latest_ids = email_ids[-limit:]
        results = []
        for e_id in reversed(latest_ids):
            status, msg_data = mail.fetch(e_id, "(RFC822)")
            if status == "OK":
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
                                "body_preview": body[:500] + ("..." if len(body) > 500 else "")
                            })
                        except:
                            pass
        mail.logout()
        return json.dumps({"status": "success", "emails": results}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"获取邮件时发生错误：{str(e)}"

if __name__ == "__main__":
    mcp.run()