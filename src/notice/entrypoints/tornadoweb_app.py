#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import tornado.web
from tornado.ioloop import IOLoop
from src.notice.entrypoints.apis import HealthCheck, Ping
from src.notice.entrypoints.apis.notice import SendSMS, SendMail
from config import CONF

logger = logging.getLogger(__name__)


def make_app():
    return tornado.web.Application([
        (r"/api/healthz", HealthCheck),
        (r"/api/ping", Ping),

        (r"/api/eyw/send_sms", SendSMS),
        (r"/api/eyw/send_mail", SendMail),
    ])


def initialize_web_app():
    app = make_app()
    app.listen(port=CONF.get('api', {}).get('port', '8080'), address=CONF.get('api', {}).get('host', '0.0.0.0'))
    logger.info('启动http服务suc...')
    IOLoop.instance().start()
