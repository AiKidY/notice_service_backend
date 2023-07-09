#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging.config
import os

from src.seedwork.utils.context import context_request_id

if not os.path.isdir('logs'):
    os.mkdir('logs')

logdir, _ = os.path.split(os.path.abspath(__file__))
log_conf_path = logdir + '/etc/log.conf'
logging.config.fileConfig(log_conf_path)
logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
logging.getLogger("pika").setLevel(logging.WARNING)
logging.getLogger('apscheduler').setLevel(logging.WARNING)


class MyFilter(logging.Filter):
    def filter(self, record):
        request_id = ""
        try:
            request_id = context_request_id.get("-")
        except Exception as e:
            pass
        record.request_id = request_id
        return True


my_filter = MyFilter()
for handler in logging.getLogger().handlers:
    handler.addFilter(my_filter)
