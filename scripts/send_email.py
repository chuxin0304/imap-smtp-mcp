#!/usr/bin/env python3
import sys
import os
import json
import smtplib
import argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(username, password, smtp_server, to_addrs, subject, body):
    try:
        # 准备邮件内容
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = to_addrs
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # 连接到 SMTP 服务器
        server = smtplib.SMTP_SSL(smtp_server, 465)
        server.login(username, password)
        
        # 发送邮件
        recipients = [email.strip() for email in to_addrs.split(',')]
        server.send_message(msg, from_addr=username, to_addrs=recipients)
        server.quit()
        
        print(json.dumps({
            "status": "success", 
            "message": "邮件发送成功",
            "to": recipients,
            "subject": subject
        }, ensure_ascii=False, indent=2))
        
    except smtplib.SMTPAuthenticationError as e:
        print(json.dumps({
            "error": "SMTP 认证失败", 
            "details": str(e), 
            "help": f"请检查 config.json 中的账号或授权码是否正确，服务器 {smtp_server} 是否可用，且确保在网页版设置中已开启 SMTP 服务。"
        }, ensure_ascii=False))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"发生错误: {str(e)}"}, ensure_ascii=False))
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="发送邮件")
    parser.add_argument('--username', required=True)
    parser.add_argument('--password', required=True)
    parser.add_argument('--smtp_server', required=True)
    parser.add_argument('--to', required=True)
    parser.add_argument('--subject', required=True)
    parser.add_argument('--body', required=True)
    args = parser.parse_args()
    send_email(args.username, args.password, args.smtp_server, args.to, args.subject, args.body)
