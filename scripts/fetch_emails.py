#!/usr/bin/env python3
import sys
import os
import argparse
import imaplib
import email
from email.header import decode_header
import json
import logging

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

def fetch_emails(username, password, imap_server="imap.qiye.163.com", limit=5, folder="inbox"):
    try:
        # Connect to server
        mail = imaplib.IMAP4_SSL(imap_server, 993)
        mail.login(username, password)
        mail.select(f'"{folder}"')
        
        # Search for all emails
        status, messages = mail.search(None, "ALL")
        if status != "OK":
            print(json.dumps({"error": "无法获取邮件列表"}))
            return
            
        email_ids = messages[0].split()
        if not email_ids:
             print(json.dumps({"status": "success", "emails": [], "message": "邮箱是空的"}))
             return
             
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
                            "body": body[:1000] + ("..." if len(body) > 1000 else "") # Limit length to prevent massive output
                        })
                    except Exception as parse_e:
                        logging.warning(f"Failed to parse email {e_id}: {parse_e}")
                        
        mail.logout()
        print(json.dumps({"status": "success", "emails": results}, ensure_ascii=False, indent=2))
        
    except imaplib.IMAP4.error as e:
        print(json.dumps({"error": f"IMAP 认证或连接失败", "details": str(e), "help": f"请检查 config.json 中的账号或授权码是否正确，服务器 {imap_server} 是否可用，且确保在网页版设置中已开启 IMAP 服务。"}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": f"发生错误: {str(e)}"}, ensure_ascii=False))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="获取邮件")
    parser.add_argument('--username', required=True)
    parser.add_argument('--password', required=True)
    parser.add_argument('--imap_server', required=True)
    parser.add_argument('--limit', type=int, default=5)
    parser.add_argument('--folder', default="inbox")
    args = parser.parse_args()
    fetch_emails(args.username, args.password, args.imap_server, args.limit, args.folder)
