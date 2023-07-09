#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import logging
import demjson3
import traceback
import tornado.web
from src.notice.domain import commands
from src.utils.common import check_recv_params

from src.notice.utils import JsonCustomEncoder

logger = logging.getLogger(__name__)


def get_resp():
    return {"code": 0, "message": "success"}


def parse_recv_params(request):
    parse_params = {}
    try:
        recv_params = request.arguments
        params = {x: recv_params.get(x)[0].decode("utf-8") for x in recv_params.keys()}
        if not params:
            body = request.body.decode('utf-8')
            parse_params = json.loads(body) if body else {}
        else:
            for key, value in params.items():
                _value = value
                if type(value) != dict:
                    try:
                        _value = demjson3.decode(value, encoding='utf-8')
                    except:
                        pass
                parse_params[key] = _value
    except Exception:
        logger.error(f'parse_recv_params, error: {traceback.format_exc()}')
    finally:
        logger.info(f'parse_recv_params, parse_params: {parse_params}')
        return parse_params


class BaseHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header(
            "Access-Control-Allow-Headers", "*"
        )  # 这里要填写上请求带过来的Access-Control-Allow-Headers参数，如access_token就是我请求带过来的参数
        self.set_header(
            "Access-Control-Allow-Methods", "POST, GET, OPTIONS, DELETE"
        )  # 请求允许的方法
        self.set_header(
            "Access-Control-Max-Age", "3600"
        )  # 用来指定本次预检请求的有效期，单位为秒，，在此期间不用发出另一条预检请求。

    def options(self):
        # 返回方法1
        self.set_status(204)
        self.finish()


class HealthCheck(BaseHandler):
    async def get(self):
        logger.info('_health_check, 健康检查')
        resp = get_resp()
        self.write(json.dumps(resp))


class Ping(BaseHandler):
    async def get(self):
        await self._handler()

    async def post(self):
        await self._handler()

    async def _handler(self):
        params = parse_recv_params(self.request)
        flag, resp = check_recv_params(params, commands.Ping)
        serialize_result = json.dumps(resp, cls=JsonCustomEncoder, ensure_ascii='utf-8')
        self.write(demjson3.decode(json.dumps(serialize_result)))
