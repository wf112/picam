# !/usr/env/bin python
# coding=utf-8

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication


# 向指定邮箱发送邮件
def send_email(address, jpgname):
    msg_from = '15623403637@163.com'  # 发送方邮箱
    password = 'wangfan1997'       # 发送方邮箱的授权码
    msg_to = address                  # 收件人邮箱

    # 构造邮件
    subject = "树莓派信息"
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = msg_from
    msg['To'] = msg_to
    
    puretext = MIMEText('Intrusion information alarm')
    msg.attach(puretext)
    
    jpgpart = MIMEApplication(open(jpgname, 'rb').read())
    jpgpart.add_header('Content-Disposition', 'attachment', filename=jpgname)
    msg.attach(jpgpart)
 
    s = smtplib.SMTP_SSL("smtp.163.com", 465)
    s.login(msg_from, password)
    s.sendmail(msg_from, msg_to, msg.as_string())
    s.quit()
    return True