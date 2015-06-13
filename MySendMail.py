# -*- coding: utf-8 -*-
"""
Created on Sat Jun 06 13:13:05 2015

@author: Craig
"""

import smtplib
import email.utils
from email.mime.text import MIMEText
import curtinSMTP as env

def MySendMail(Subject, Body):
    '''MySendMail() uses gmail to send out email'''
    # recipients are a list of email addresses
    #recipients = ['curtin1060@gmail.com', 'jimcurtin3@gmail.com']
    recipients = ['curtin1060@gmail.com', 'kevin.curtin@alumni.msoe.edu' ]
    recipients = ['curtin1060@gmail.com' ]
    fromaddr = 'craig.s.curtin@gmail.com'
    toaddrs = recipients
    
    msg=MIMEText(Body)
    msg['Subject'] = Subject
    msg['From'] = fromaddr
    msg['To'] = ", ".join(recipients)
    username = env.username
    password = env.password
    server = smtplib.SMTP(env.smtpHost)
    server.ehlo()
    server.starttls()
    server.login(username, password)
    server.sendmail(fromaddr, toaddrs, msg.as_string())
    server.quit()
    return
