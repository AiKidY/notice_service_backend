#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import initlog
import config
import logging
from lycium.dbproxy import DbProxy
from lycium.amqplib import RabbitMQFactory

from config import CONF
from src.notice.utils import const
from src.notice.entrypoints.tornadoweb_app import initialize_web_app

logger = logging.getLogger(__name__)


class Main(object):
    def __init__(self):
        self.amqp_factory = RabbitMQFactory()
        self.rabconfs = [config.rabbitmq_eyw]
        self.module_map = const.module_map

    def init(self):
        logger.info('main程序启动...')
        if CONF.get('rdbms'):
            DbProxy().setup_rdbms(CONF.get('rdbms'))

        for rabconf in self.rabconfs:
            self.amqp_factory.initialize({
                'host': rabconf.get('host'),
                'port': rabconf.get('port'),
                'username': rabconf.get('username'),
                'password': rabconf.get('password'),
                'virtual_host': rabconf.get('virtual_host'),
                'sock_timeout': rabconf.get('sock_timeout'),
                'heartbeat': rabconf.get('heartbeat')
            })

        for m_name, m_func in self.module_map.items():
            logger.info('starting module %s...', m_name)
            m_func()

        logger.info('mq start running...')
        self.amqp_factory.run()
        initialize_web_app()


if __name__ == '__main__':
    obj = Main()
    obj.init()
