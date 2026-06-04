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
    parser = argparse.ArgumentParser(description="发送网易企业邮箱/126邮箱邮件")
    parser.add_argument('--to', required=True, help="收件人邮箱地址（多个收件人用逗号分隔）")
    parser.add_argument('--subject', required=True, help="邮件主题")
    parser.add_argument('--body', required=True, help="邮件正文")
    args = parser.parse_args()

    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    username = None
    password = None
    smtp_server = None

    # 读取配置文件
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                username = config.get("email_address")
                password = config.get("auth_code")
                smtp_server = config.get("smtp_server")
        except Exception as e:
            pass

    if not username or not password or not smtp_server or username == "your_email@example.com" or password == "your_auth_code_here":
        print(json.dumps({
            "error": "未配置有效的邮箱账号或授权码。",
            "help": f"请打开 {os.path.abspath(config_path)} 并填入正确的 email_address 和 auth_code。"
        }, ensure_ascii=False))
        sys.exit(1)
        
    send_email(username, password, smtp_server, args.to, args.subject, args.body)