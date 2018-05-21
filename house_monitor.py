#!/usr/bin/python3

from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
import smtplib
from html.parser import HTMLParser
import requests
from datetime import datetime
import time
from apscheduler.schedulers.blocking import BlockingScheduler
import os
import logging

def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))

def Send_email(content, from_addr='18117510016@189.cn',
               password='gaupen11860016',
               to_addr='18117510016@189.cn',
               smtp_server='smtp.189.cn'):
    smtp_port = 25

    mail = MIMEText(content, 'plain', 'utf-8')
    mail['From'] = _format_addr('<%s>' % from_addr)
    mail['To'] = _format_addr('<%s>' % to_addr)
    mail['Subject'] = Header('房源更新通知', 'utf-8').encode()

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.set_debuglevel(0)
        server.login(from_addr, password)
        server.sendmail(from_addr, [to_addr], mail.as_string())
    except:
        tmp_log = 'Send email failed.'
        logger.error('%s %s' % (str(datetime.now()), tmp_log))
        print('%s %s' % (str(datetime.now()), tmp_log))
    else:
        server.quit()
        tmp_log = 'E-mail has been sent.'
        logger.info('%s %s' % (str(datetime.now()), tmp_log))
        print('%s %s' % (str(datetime.now()), tmp_log))

#定义HTMLParser的子类,用以复写HTMLParser中的方法
class MyHTMLParser(HTMLParser):
    #构造方法,定义data数组用来存储html中的数据
    def __init__(self):
        self.handledtags = ['span', 'p', 'a']
        self.processing = None
        self.data = []
        HTMLParser.__init__(self)

    #覆盖starttag方法,可以进行一些打印操作
    def handle_starttag(self, tag, attrs):
        #print('<%s>' % tag)
        if tag in self.handledtags:
            self.processing = tag
        else:
            self.processing =None

    def handle_data(self, data):
        if self.processing=='span':
            self.data.append(data)
            #print( self.data[0] )

    def handle_endtag(self, tag):
        pass
        #print('</%s>' % tag)

    def handle_startendtag(self, tag, attrs):
        pass
        #print('<%s/>' % tag)

def job_func():
    global html_content
    global network_error
    global url
    global last_result
    global new_result
    global parser
    global loop_cnt
    global first_excute

    tmp_log = 'Loop counter = %d' %loop_cnt
    logger.info('%s %s' % (str(datetime.now()), tmp_log))
    print('%s %s' % (str(datetime.now()), tmp_log))

    try:
        html_content = requests.get(url)
        network_error = False
    except IOError as e:
        network_error = True
        print('%s %s' % (str(datetime.now()), e))
        Send_email(str(e))

    if network_error!=True and html_content!=None:
        # 创建子类实例
        parser = MyHTMLParser()
        # 将html数据传给解析器进行解析
        parser.feed(html_content.text)
        parser.close()

        # 字符串长度检查
        if len(parser.data[0])>0:
            new_result = parser.data[0]
        else:
            tmp_log = '获取到的公告字符串为空'
            send_email(tmp_log)
            logger.error('%s %s' % (str(datetime.now()), tmp_log))
            print('%s %s' % (str(datetime.now()), tmp_log))

        # 判断比较
        #不是第一次运行
        if first_excute!=True:
            if len(new_result)!=0 and len(last_result)!=0:
                if new_result==last_result:
                    tmp_log = '公告无更新'
                    Send_email(tmp_log)
                    print('%s %s' % (str(datetime.now()), tmp_log))
                    logger.info(tmp_log)
                else:
                    tmp_log = '有新公告请尽快查看：%s' %new_result
                    Send_email(tmp_log)
                    print('%s %s' % (str(datetime.now()), tmp_log))
                    logger.info(tmp_log)
        # 第一次运行
        else:
            first_excute = False
            tmp_log = '首次运行，公告：%s' %new_result
            Send_email(tmp_log)
            logger.info(tmp_log)
            print('%s %s' % (str(datetime.now()), tmp_log))

        loop_cnt +=1
        last_result = parser.data[0]

url = 'http://www.shcngz.com/pages/news_list.aspx?mid=29'
last_result = ''
new_result = ''
network_error = False
tmp_log = ''
loop_cnt = 1
first_excute = True
html_content = None

if __name__ == '__main__':

    # create logger
    logger_name = "log"
    log_path = "./log.log"
    fmt = "【%(asctime)-15s %(levelname)s】 %(message)s"
    datefmt = "%Y/%m/%d %H:%M:%S"

    logger = logging.getLogger(logger_name)
    fileHandler = logging.FileHandler(log_path)
    formatter = logging.Formatter(fmt, datefmt)

    logger.setLevel(logging.DEBUG)
    fileHandler.setLevel(logging.DEBUG)
    fileHandler.setFormatter(formatter)
    logger.addHandler(fileHandler)

    scheduler = BlockingScheduler()
    #scheduler.add_job(job_func, 'cron', hour='0-23', minute=5)
    scheduler.add_job(job_func, 'cron', hour='0-23', second='0,30')
    scheduler.start()
