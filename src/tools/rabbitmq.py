#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import pika

logger = logging.getLogger(__name__)


class RabMQProducer(object):
    def __init__(self,
                 host='127.0.0.1',
                 port=5672,
                 virtual_host='/',
                 heartbeat=30,
                 connection_attempts=3,
                 username='guest',
                 password='guest'):

        self._durable = None
        self._exchange = None

        credentials = pika.PlainCredentials(username, password)
        self._url = pika.ConnectionParameters(host=host,
                                              port=port,
                                              virtual_host=virtual_host,
                                              credentials=credentials,
                                              heartbeat=heartbeat)

        self._conn = None
        self._channel = None
        self._all_exchange = {}

        self._exchange_name = None
        self._exchange_type = 'direct'
        self._queue_name = []
        self._routingkey = []
        self._durable = True
        self._connection_attempts = connection_attempts
        self._rk_q_dic = {}

        self.connect()

    def connect(self):
        self._conn = pika.BlockingConnection(self._url)
        self._channel = self._conn.channel()

    def publish(self, exchange, routingkey, body, exchange_type='topic', durable=True):
        if self._conn and self._conn.is_open and self._channel.is_open:
            try:
                logger.info(f"RabMQProducer publish, exchange: {exchange}, routingkey: {routingkey}, body: {body}")
                self._channel.exchange_declare(exchange=exchange, exchange_type=exchange_type, durable=durable)
            except:
                logger.error(f'RabMQProducer publish, exchange declare except, reconnectd...')
            try:
                if durable:
                    self._channel.basic_publish(
                        exchange=exchange,
                        routing_key=routingkey,
                        body=body,
                        properties=pika.BasicProperties(delivery_mode=2))
                else:
                    self._channel.basic_publish(
                        exchange=exchange,
                        routing_key=routingkey,
                        body=body)

                self._connection_attempts = 3
            except:
                logger.error(f'RabMQProducer publish, send msg except, reconnectd...')
                self.reconnt(exchange, routingkey, body, exchange_type, durable)
        else:
            self.reconnt(exchange, routingkey, body, exchange_type, durable)

    def reconnt(self, exchange, routingkey, body, exchange_type, durable):
        self._connection_attempts -= 1
        if self._connection_attempts < 0:
            raise SyntaxError('connect mq error')

        self.close()
        self.connect()
        self.publish(exchange, routingkey, body, exchange_type, durable)

    def init(self, exchange, exchange_type, queuename=None, routing_keys=None, durable=True):
        if self._exchange_name and self._exchange_name != exchange:
            raise ValueError("only support one exchange")

        if self._exchange_type:
            self._exchange_type = exchange_type

        tmpkeys = []
        if isinstance(routing_keys, list):
            tmpkeys = routing_keys
            self._routingkey += routing_keys
            for rk in routing_keys:
                self._rk_q_dic[rk] = queuename

        elif isinstance(routing_keys, str):
            self._routingkey.append(routing_keys)
            self._rk_q_dic[routing_keys] = queuename
            tmpkeys.append(routing_keys)

        self._durable = durable

        if not self._exchange_name:
            self._exchange_name = exchange
            self.exchange_declare()

        if isinstance(queuename, str):
            if not queuename in self._queue_name:
                self._queue_name.append(queuename)

            self.queue_declare(queuename, tmpkeys)

    def exchange_declare(self):
        self._channel.exchange_declare(
            exchange=self._exchange_name,
            exchange_type=self._exchange_type,
            durable=self._durable)

    def queue_declare(self, queuename, rks):

        self.binding_queue(queuename)

        # exchange, queue, bind
        for rk in rks:
            self.binding_queue_rk(queuename, rk)

    def binding_queue(self, queue):
        if queue:
            self._channel.queue_declare(queue=queue, durable=self._durable)

    def binding_queue_rk(self, queue_name, rk):
        self._channel.queue_bind(exchange=self._exchange_name, queue=queue_name, routing_key=rk)

    def close(self):
        """
        close
        """
        # if self._conn and self._conn.is_open:
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                logger.error(f'RabMQProducer close connect except...')
                pass
