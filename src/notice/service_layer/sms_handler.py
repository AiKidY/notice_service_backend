#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 短信相关

import logging
import time
import json
import traceback
import requests
import urllib
from lycium.amqplib import RabbitMQFactory
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest

import config
from src.notice.domain import commands
from src.notice.service_layer import unit_of_work
from src.utils.common import check_recv_params, generate_unique_identification
from src.notice.domain.model.noticerecords import NoticeRecords

logger = logging.getLogger(__name__)


class SMS():
    def init_load(self):
        self.rabconf = config.rabbitmq_eyw
        self.msgconf = config.sms_mq_consume
        self.uow = unit_of_work.MotorUnitOfWork()

    def get_resp(self):
        return {
            'code': '-1',
            'message': 'SMS sending failed'
        }

    def consume(self):
        try:
            logger.info('sms_consume starting...')
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
            logger.error(f'sms_consume, error: {e}')

    async def callback_handler(self, channel, method, properties, body):
        try:
            logger.info("sms_callback_handler, received a message by routing_key:%s, data: %r", method.routing_key,
                        str(body, encoding="utf-8"))
            body = body if isinstance(body, dict) else json.loads(body)
            flag, resp = check_recv_params(body, commands.SendMail)
            if not flag: return resp
            await self.notice(body, True)
        except Exception as e:
            logger.error(f'sms_callback_handler, error: {e}')
            # channel.basic_ack(delivery_tag=method.delivery_tag)

    async def notice(self, body, is_init=False):
        resp = self.get_resp()
        try:
            if not is_init: self.init_load()
            async with self.uow:
                if 'SignName' in body:
                    TemplateParam = body['content']
                    PhoneNumbers = body["usernumber"]
                    SignName = body["SignName"]
                    TemplateCode = body["TemplateCode"]

                    # 调用阿里云短信接口
                    flag, send_rs = await self.send_aliyun_sms(TemplateParam, PhoneNumbers, SignName, TemplateCode)
                    err = send_rs.get('errorMsg', '')
                    requestid = send_rs.get('requestid', '')

                    await self.uow.notice_records.insert_one(NoticeRecords(id=requestid,
                                                                           notice_type='sms',
                                                                           status=flag,
                                                                           status_msg=err))
                    if flag:
                        resp.update({
                            'code': '1',
                            'message': 'SMS sending success'
                        })
                    else:
                        resp.update({
                            'code': '-1',
                            'message': 'SMS sending failed with err: %s' % err
                        })
                else:
                    MessageContent = body.get('content', '')
                    UserNumber = body.get('usernumber', '')

                    # 调用联通短信接口
                    flag, send_rs = await self.send_unicom_sms(MessageContent, UserNumber)
                    errorMsg = send_rs.get('errorMsg', '')

                    await self.uow.notice_records.insert_one(NoticeRecords(id=generate_unique_identification(),
                                                                           notice_type='sms',
                                                                           status=flag,
                                                                           status_msg=errorMsg))

                    if flag:
                        resp.update({
                            'code': '1',
                            'message': 'SMS sending succeed'
                        })
                    else:
                        resp.update({
                            'code': '-1',
                            'message': 'SMS sending failed with err: %s' % errorMsg
                        })
        except Exception as e:
            logger.error(f'sms_notice, error: {e}')
            resp.update({
                'code': '-1',
                'message': 'SMS sending failed with err: %s' % str(e)
            })
        finally:
            return resp

    async def send_aliyun_sms(self, TemplateParam, PhoneNumbers, SignName, TemplateCode):
        flag, send_rs = False, {}
        try:
            sc = config.sms_cfg
            client = AcsClient(sc.get('aliyun_accesskeyid'), sc.get('aliyun_accesssecret'), sc.get('cn-hangzhou'))
            request = CommonRequest()
            request.set_accept_format(sc.get('aliyun_accept_format'))
            request.set_domain(sc.get('aliyun_domain'))
            request.set_method('POST')
            request.set_protocol_type('https')  # https | http
            request.set_version(sc.get('aliyun_version'))
            request.set_action_name('SendSms')
            request.add_query_param('TemplateParam', TemplateParam)
            request.add_query_param('PhoneNumbers', PhoneNumbers)
            request.add_query_param('SignName', SignName)
            request.add_query_param('TemplateCode', TemplateCode)
            response = json.loads(client.do_action(request).decode('utf-8'))

            send_rs = {
                'requestid': response.get('RequestId'),
                'code': response.get('Code'),
                'errorMsg': response.get('Message'),
            }

            if response.get('Code') == 'OK':
                flag = True
            else:
                flag = False
        except Exception as e:
            logger.error(f'send_aliyun_sms, error: {e}')
        finally:
            logger.info(f'send_aliyun_sms, flag: {flag}, send_rs: {send_rs}')
            return flag, send_rs

    async def send_unicom_sms(self, MessageContent, UserNumber, SerialNumber='',
                              ScheduleTime='', ExtendAccessNum='', f=''):
        flag, send_rs = False, {}
        try:
            sc = config.sms_cfg
            _ApiUrl = sc.get('cucc_apiurl')  # 发送短信接口地址
            _SpCode = sc.get('cucc_spcode')
            _LoginName = sc.get('cucc_loginame')
            _Password = sc.get('cucc_password')

            data = {
                "SpCode": _SpCode,
                "LoginName": _LoginName,
                "Password": _Password,
                # "MessageContent" : MessageContent.decode('utf-8').encode('gbk'),
                "MessageContent": MessageContent.encode('gbk'),
                "UserNumber": UserNumber,
                "SerialNumber": SerialNumber,
                "ScheduleTime": ScheduleTime,
                "ExtendAccessNum": ExtendAccessNum,
                "f": f
            }
            res = requests.post(_ApiUrl, data=data, proxies=config.proxies)
            if res.status_code != 200 or not res.text:
                flag = False
                send_rs.update({
                    'errorMsg': '未知错误'
                })
            else:
                res_dict = self.parse_unicom_sms_rs(res)
                if len(res_dict['result']) > 0 and res_dict['result'][0] == '0':
                    flag = True
                    send_rs.update({
                        'errorMsg': '成功'
                    })
                else:
                    flag = False
                    send_rs.update({
                        'errorMsg': res_dict.get('description', '')
                    })
        except Exception as e:
            logger.error(f'send_unicom_sms, error: {e}')
            flag = False
            send_rs.update({
                'errorMsg': traceback.format_exc()
            })
        finally:
            logger.info(f'send_unicom_sms, flag: {flag}, send_rs: {send_rs}')
            return flag, send_rs

    def parse_unicom_sms_rs(self, res):
        res_dict = {}
        try:
            res_dict = urllib.parse.parse_qs(res.text)
            description_list = res_dict['description']
            if res.apparent_encoding:
                description_list = [item.encode(res.apparent_encoding).decode('gbk', 'ignore') for item in
                                    description_list]
            description = ','.join(description_list)
            res_dict.update({
                'description': description
            })
        except Exception as e:
            logger.error(f'parse_unicom_sms_rs, error: {e}')
        finally:
            logger.info(f'parse_unicom_sms_rs, apparent_encoding: {res.apparent_encoding}, res_dict: {res_dict}')
            return res_dict
