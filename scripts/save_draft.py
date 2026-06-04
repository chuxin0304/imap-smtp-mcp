#!/usr/bin/env python3
import sys
import os
import json
import imaplib
import argparse
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate

def save_draft(username, password, imap_server, to_addrs, subject, body):
    try:
        # 准备邮件内容
        msg = MIMEMultipart()
        msg['From'] = username
        if to_addrs:
            msg['To'] = to_addrs
        msg['Subject'] = subject
        msg['Date'] = formatdate(localtime=True)
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # 连接到 IMAP 服务器
        mail = imaplib.IMAP4_SSL(imap_server, 993)
        mail.login(username, password)
        
        # 将邮件转为字节
        msg_bytes = msg.as_bytes()
        internal_date = imaplib.Time2Internaldate(time.time())
        
        # 使用 APPEND 将邮件追加到草稿箱文件夹，带上 \Draft 标签
        # 163/126 邮箱的草稿箱通常在 IMAP 中叫做 "Drafts"
        status, response = mail.append("Drafts", '(\\Draft)', internal_date, msg_bytes)
        
        if status != 'OK':
            # 如果英文 Drafts 失败，尝试 163 邮箱的中文草稿箱 UTF-7-IMAP 编码 "&g0l6P3ux-"
            status, response = mail.append("&g0l6P3ux-", '(\\Draft)', internal_date, msg_bytes)
            if status != 'OK':
                raise Exception(f"Failed to append to draft folder: {response}")

        mail.logout()
        
        print(json.dumps({
            "status": "success", 
            "message": "邮件已成功保存到草稿箱",
            "subject": subject
        }, ensure_ascii=False, indent=2))
        
    except imaplib.IMAP4.error as e:
        print(json.dumps({
            "error": "IMAP 认证失败或文件夹不存在", 
            "details": str(e), 
            "help": f"请检查 config.json 中的账号和授权码，以及确保在网页端设置中已开启 IMAP 服务。"
        }, ensure_ascii=False))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"发生错误: {str(e)}"}, ensure_ascii=False))
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="保存草稿")
    parser.add_argument('--username', required=True)
    parser.add_argument('--password', required=True)
    parser.add_argument('--imap_server', required=True)
    parser.add_argument('--to', required=False, default="")
    parser.add_argument('--subject', required=True)
    parser.add_argument('--body', required=True)
    args = parser.parse_args()
    save_draft(args.username, args.password, args.imap_server, args.to, args.subject, args.body)
