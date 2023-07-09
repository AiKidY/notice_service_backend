#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import logging
import config
import pika
from lycium.amqplib import RabbitMQFactory

logger = logging.getLogger(__name__)


class PublishRabbitmq():
    def nanxunmen_publish_handler(self, msg, correlation_id, properties):
        # logger.info(f'nanxunmen_publish_handler, traceId: {properties.headers.get("traceId")}, msg: {msg}')

        rabconf = config.rabbitmq_eyw
        msgconf = config.nanxunmen_cfg
        producer_mq = RabbitMQFactory()
        producer_conf = msgconf.get('publish')
        producer_mq.publish(
            virtual_host=rabconf.get('virtual_host'),
            exchange='',
            routing_key=properties.reply_to if properties.reply_to else producer_conf.get('routing_keys').get("ss"),
            message=json.dumps(msg).encode('utf-8'),
            properties=pika.BasicProperties(correlation_id=correlation_id)
        )
        logger.info("nanxunmen_publish_handler, message is published and ack!")
