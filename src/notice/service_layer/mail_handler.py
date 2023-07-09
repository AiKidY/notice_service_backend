#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 邮件相关

import os
import logging
import json
import traceback
import ssl
import smtplib
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from lycium.amqplib import RabbitMQFactory

import config
from src.notice.service_layer import unit_of_work
from src.utils.common import check_recv_params, generate_unique_identification
from src.notice.domain.model.noticerecords import NoticeRecords
from src.notice.domain import commands

logger = logging.getLogger(__name__)


class Mail():
    def init_load(self):
        self.rabconf = config.rabbitmq_eyw
        self.msgconf = config.mail_mq_consume
        self.mailconf = config.mail_cfg
        self.uow = unit_of_work.MotorUnitOfWork()

    def get_resp(self):
        return {
            'code': '-1',
            'message': 'mail sending failed'
        }

    def consume(self):
        try:
            logger.info('mail_consume starting...')
            self.init_load()
            mq_factory = RabbitMQFactory()
            mq_factory.consume(
                virtual_host=self.rabconf['virtual_host'],
                exchange=self.msgconf['exchange'],
                exchange_type=self.msgconf['exchange_type'],
                binding_key=self.msgconf['routing_keys'],
                queue=self.msgconf['queue']['sms_receivemessage'],
                durable=self.msgconf['durable'],
                callback=self.callback_handler,
                auto_ack=True
            )
        except Exception as e:
            logger.error(f'mail_consume, error: {e}')

    async def callback_handler(self, channel, method, properties, body):
        try:
            logger.info("mail_callback_handler, received a message by routing_key:%s, data: %r", method.routing_key,
                        str(body, encoding="utf-8"))
            body = body if isinstance(body, dict) else json.loads(body)
            flag, resp = check_recv_params(body, commands.SendMail)
            if not flag: return resp
            await self.notice(body, True)
        except Exception as e:
            logger.error(f'mail_callback_handler, error: {e}')
            # channel.basic_ack(delivery_tag=method.delivery_tag)

    async def notice(self, params, is_init=False):
        resp = self.get_resp()
        try:
            if not is_init: self.init_load()
            async with self.uow:
                resp = await self.send_mail(params)
                await self.uow.notice_records.insert_one(NoticeRecords(id=generate_unique_identification(),
                                                                       notice_type='mail',
                                                                       status=True if resp.get('code') == 0 else False,
                                                                       status_msg=resp.get('message', '')))
        except Exception as e:
            logger.error(f'mail_notice, error: {e}')
            resp.update({
                'code': '500',
                'message': 'mail sending failed with err: %s' % str(e)
            })
        finally:
            logger.info(f'mail_notice, params: {params}, resp: {resp}')
            return resp

    async def send_mail(self, recv_data):
        resp = self.get_resp()
        try:
            mail_classify = str(recv_data.get('mail_classify'))
            if mail_classify == '163':
                resp = await self.send_163_mail(recv_data)
            elif mail_classify == 'qq':
                resp = await self.send_qq_mail(recv_data)
            else:
                resp.update({'message': f'不支持的邮件类型[{mail_classify}],请检查!'})
        except Exception as e:
            logger.error(f'send_mail, error: {e}')
        finally:
            return resp

    async def send_163_mail(self, recv_data):
        resp = self.get_resp()
        try:
            mail_conf = self.mailconf.get(163, {})
            logger.info(f'send_163_mail, mail_conf: {mail_conf}, recv_data: {recv_data}')

            smtp_host = mail_conf.get('smtp_host')  # 163邮件服务器的地址
            smtp_port = int(mail_conf.get('smtp_port'))  # 安全端口
            sender = recv_data.get('sender')  # 发件人
            receivers = recv_data.get('receivers', [])  # 收件人邮箱地址，列表中可以包含多个收件人地址
            # 163邮件服务器的授权码(未传取默认的)
            authorize_code = recv_data.get('authorize_code', '')
            authorize_code = mail_conf.get('authorize_code') if not authorize_code else authorize_code
            subject = recv_data.get('subject')  # 主题
            mail_type = recv_data.get('mail_type', '') if recv_data.get('mail_type', '') else 'html'
            mail_text = recv_data.get('mail_text')
            mail_attachments = recv_data.get('mail_attachments', [])

            # 连接邮箱服务器
            with smtplib.SMTP_SSL(smtp_host, int(smtp_port)) as con:
                # 登录邮箱
                con.login(sender, authorize_code)
                # 准备数据
                # 创建邮件对象
                msg = MIMEMultipart('related')
                # 设置邮件主题
                subject = Header(subject, 'utf-8').encode()
                msg['Subject'] = subject
                # 设置邮件发送者
                msg['From'] = sender
                # 设置邮件接受者
                msg['To'] = ','.join(receivers)

                if mail_type == 'plain':
                    text = MIMEText(mail_text, 'plain', 'utf-8')
                elif mail_type == 'html':
                    text = MIMEText(mail_text, 'html', 'utf-8')
                # 添加文字内容
                msg.attach(text)

                # 添加附件
                for mail_attachment_path in mail_attachments:
                    if not os.path.exists(mail_attachment_path):
                        resp.update({'code': -1, 'message': f'{mail_attachment_path} file not exist, please check!'})
                        return resp

                    # 以二进制方式打开指定文件
                    with open(r'%s' % mail_attachment_path, 'rb') as file:
                        att = MIMEText(file.read(), 'base64', 'utf-8')
                        # 设置文件的内容格式
                        att['Content-Type'] = 'application/octet-stream'
                        # 所以附件名称为中文时的写法如下
                        att.add_header('Content-Disposition', 'attachment',
                                       filename=('gbk', '', mail_attachment_path))
                        msg.attach(att)
                # 发送邮件
                con.sendmail(sender, receivers, msg.as_string())
            resp.update({'code': 0, 'message': '163 mail send success!'})
        except Exception as e:
            logger.error(f'send_163_mail, error: {e}')
            resp.update({
                'code': 500,
                'message': traceback.format_exc()
            })
        finally:
            logger.info(f'send_163_mail, resp: {resp}')
            return resp

    async def send_qq_mail(self, recv_data):
        resp = self.get_resp()
        try:
            mail_conf = self.mailconf.get('qq', {})
            logger.info(f'send_qq_mail, mail_conf: {mail_conf}, recv_data: {recv_data}')

            smtp_host = mail_conf.get('smtp_host')  # QQ邮件服务器的地址
            smtp_port = int(mail_conf.get('smtp_port'))  # 安全端口
            # QQ邮件服务器的授权码(未传取默认的)
            authorize_code = recv_data.get('authorize_code', '')
            authorize_code = mail_conf.get('authorize_code') if not authorize_code else authorize_code
            sender = recv_data.get('sender')  # 发件人
            receivers = recv_data.get('receivers', [])  # 收件人邮箱地址，列表中可以包含多个收件人地址
            carbon_cper = recv_data.get('carbon_cper', [])  # 抄送人邮箱地址，列表中可以包含多个抄送人地址
            bcarbn_cper = recv_data.get('bcarbn_cper', [])  # 密送人邮箱地址，列表中可以包含多个密送人地址
            subject = recv_data.get('subject')  # 主题
            mail_type = recv_data.get('mail_type', '') if recv_data.get('mail_type', '') else 'html'
            mail_text = recv_data.get('mail_content', '')
            mail_attachments = recv_data.get('mail_attachments', [])

            # 构造邮件头
            # 构造一个富文本的邮件体
            email_msg = MIMEMultipart('mixed')
            # 构造邮件头中主题，突出邮件内容重点
            email_msg['Subject'] = Header(subject, 'utf-8').encode()
            # 构造邮件头中的发件人，包括昵称和邮箱账号
            email_msg['From'] = sender
            # 构造邮件头中的收件人，包括昵称和邮箱账号
            email_msg['To'] = ','.join(receivers)
            # 构造邮件头中的抄送人，包括昵称和邮箱账号
            email_msg['Cc'] = ','.join(carbon_cper)
            # 构造邮件头中的密送人，包括昵称和邮箱账号
            email_msg['Bcc'] = ','.join(bcarbn_cper)

            # 构造一个可包含text和html格式文件的邮件体(MIMEMultipart('alternative')类型的邮件体)
            alter_msg = MIMEMultipart('alternative')
            if mail_type == 'plain':
                # 构造纯文本格式的邮件内容，采用'utf-8'编码并附加到alternative邮件体
                alter_msg.attach(MIMEText(mail_text, 'plain', 'utf-8'))
            elif mail_type == 'html':
                # 采用'utf-8'编码并将html格式的内容附加到alternative邮件体
                alter_msg.attach(MIMEText(mail_text, 'html', 'utf-8'))
            # 将alternative邮件体附加到整个邮件体
            email_msg.attach(alter_msg)

            # 添加附件
            for mail_attachment_path in mail_attachments:
                if not os.path.exists(mail_attachment_path):
                    resp.update({'code': -1, 'message': f'{mail_attachment_path} file not exist, please check!'})
                    return resp

                # 以二进制方式打开指定文件
                with open(r'%s' % mail_attachment_path, 'rb') as file:
                    # 用打开的文件构造一个文件对象，注意是MIMEText对象
                    # 数据流为base64格式
                    att = MIMEText(file.read(), 'base64', 'utf-8')
                    # 设置文件的内容格式
                    att['Content-Type'] = 'application/octet-stream'
                    # 所以附件名称为中文时的写法如下
                    att.add_header('Content-Disposition', 'attachment',
                                   filename=('gbk', '', mail_attachment_path))
                    email_msg.attach(att)

            try:
                with smtplib.SMTP_SSL(smtp_host, smtp_port) as email_svr:
                    email_svr.login(sender, authorize_code)  # 输入QQ邮箱的账号和授权码后登录
                    email_svr.sendmail(sender, receivers, email_msg.as_string())  # 将MIMEText对象或MIMEMultipart对象变为str
                resp.update({'code': 0, 'message': 'qq mail send success!'})
            except smtplib.SMTPException as e:
                logger.error(f'send_qq_mail, smtp发生错误，邮件发送失败, error: {e}')
                resp.update({
                    'code': 500,
                    'message': traceback.format_exc()
                })
        except Exception as e:
            logger.error(f'send_qq_mail, error: {traceback.format_exc()}')
            resp.update({
                'code': 500,
                'message': traceback.format_exc()
            })
        finally:
            logger.info(f'send_qq_mail, recv_data: {recv_data}, resp: {resp}')
            return resp
