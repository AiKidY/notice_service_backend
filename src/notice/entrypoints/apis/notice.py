#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import json
import demjson3
from src.notice.domain import commands
from src.notice.utils import JsonCustomEncoder
from src.notice.entrypoints.apis import BaseHandler, parse_recv_params
from src.notice.utils.const import api_func_map
from src.utils.common import check_recv_params


class SendSMS(BaseHandler):
    async def post(self):
        await self._handler()

    async def _handler(self):
        params = parse_recv_params(self.request)
        flag, resp = check_recv_params(params, commands.SendSMS)
        if flag:
            resp = await api_func_map.get('sms')(params)
        serialize_result = json.dumps(resp, cls=JsonCustomEncoder, ensure_ascii='utf-8')
        self.write(demjson3.decode(json.dumps(serialize_result)))


class SendMail(BaseHandler):
    async def post(self):
        await self._handler()

    async def _handler(self):
        params = parse_recv_params(self.request)
        flag, resp = check_recv_params(params, commands.SendMail)
        if flag:
            resp = await api_func_map.get('mail')(params)
        serialize_result = json.dumps(resp, cls=JsonCustomEncoder, ensure_ascii='utf-8')
        self.write(demjson3.decode(json.dumps(serialize_result)))
