#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

import pika
from lycium.amqplib import RabbitMQFactory
from config import CONF

logger = logging.getLogger(__name__)


def send_to_ws(send_data, correlation_id=None):
    mq_factory = RabbitMQFactory()
    mq_config = CONF.amqp_consumer
    mq_factory.publish(CONF.rabbitmq["eyw"].get('virtual_host'),
                       mq_config['exchange_response']['name'],
                       mq_config.get('routing_keys')['biz'],
                       send_data,
                       pika.BasicProperties(correlation_id=correlation_id) if correlation_id else None)
    logger.info(f'send_to_ws, send_data: {send_data}')
