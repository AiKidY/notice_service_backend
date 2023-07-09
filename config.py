#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import yaml
import logging

logger = logging.getLogger(__name__)


def loadYamlConfig():
    yaml_config = dict()
    try:
        yamfile = os.getcwd() + "/etc/config.yaml"
        logger.info(f'loadYamlConfig, yamfile_path: {yamfile}')
        f = open(yamfile, 'r', encoding='utf-8')
        yaml_config = yaml.load(f.read(), Loader=yaml.SafeLoader)
        f.close()
    except Exception as e:
        logger.error(f'loadYamlConfig, error: {e}')
    return yaml_config


CONF = loadYamlConfig()
logger.info(f'loadYamlConfig finish: {CONF}')

# ------------------------------------------------------------ 配置 ------------------------------------------------------
rabbitmq_eyw = CONF.get('rabbitmq_eyw', {})
proxies = CONF.get('proxies', {})
sms_cfg = CONF.get('sms_cfg', {})
mail_cfg = CONF.get('mail_cfg', {})
api = CONF.get('api', {})

sms_mq_consume = {
    "exchange": "eyw.sms.ex.request",
    "exchange_type": "topic",
    "routing_keys": "eyw.sms.rk.request",
    "queue": {
        "sms_receivemessage": "eyw.sms.queue.request"
    },
    "durable": True
}

mail_mq_consume = {
    "exchange": "eyw.mail.ex.request",
    "exchange_type": "topic",
    "routing_keys": "eyw.mail.rk.request",
    "queue": {
        "sms_receivemessage": "eyw.mail.queue.request"
    },
    "durable": True
}
all_config_var = locals()

# ------------------------------------------------------------ 配置 ------------------------------------------------------
