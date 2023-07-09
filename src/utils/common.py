#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import logging
import json
import aiohttp
import base64
import hashlib
import traceback
import uuid
from lycium import asyncrequest
from datetime import date, datetime

from bson import ObjectId

logger = logging.getLogger(__name__)


def get_resp():
    return {"code": 0, "message": "success"}


class JsonCustomEncoder(json.JSONEncoder):
    def default(self, field):
        if isinstance(field, datetime):
            return field.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(field, date):
            return field.strftime('%Y-%m-%d')
        elif isinstance(field, ObjectId):
            return str(field)
        else:
            return json.JSONEncoder.default(self, field)


def base64_encode(val):
    if isinstance(val, bytes):
        return base64.b64encode(val).decode()
    return base64.b64encode(val.encode()).decode()


def md5_encode(val):
    m = hashlib.md5(val.encode())
    return m.hexdigest()


def sign_inputs_data_md5(app_key, params, fields=None, sign_field='sign', sorted_fields=1):
    """Signature the inputs data

    :app_key str Application signature key

    :params dict The inputs data in dict formation

    :fields list The field list that would be signatured, if attempts None, the fields would been taken params.keys()

    :sign_field str The field name that specifies signature data, this field name would be forcely skipped in params when formatting signature data.

    :sorted_fields int If > 0, the fields would be sorted increasely when formatting signature data, if < 0 the fields would be sorted reversely when formatting signature data.
    """

    if not fields:
        fields = [k for k in params.keys()]

    if sorted_fields > 0:
        fields.sort()
    elif sorted_fields < 0:
        fields.sort(reverse=True)

    signvalues = []
    for k in fields:
        if k == sign_field:
            continue
        signvalues.append(k + '=' + str(params.get(k, '')))

    signtext = '&'.join(signvalues) + app_key
    signdata = md5_encode(signtext)

    return signdata


async def send_sync_get_request(server_url, headers={}, verify_ssl=None):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=server_url, headers=headers, verify_ssl=verify_ssl) as res:
                response = await res.text()
                logger.info(
                    f"send_sync_get_request, req_url:{server_url}, headers: {headers}, status: {res.status}, data_length: {len(json.loads(response))}")
                return res.status, json.loads(response)
    except Exception as e:
        logger.error(f"send post request: {server_url} failed with err:{str(e)}")
        return None, str(e)


async def send_sync_post_request(req_url, req_params, **kwargs):
    rs = {}
    try:
        start = time.time()
        code, response = await asyncrequest.async_post_json(url=req_url, json=req_params, connect_timeout=180,
                                                            request_timeout=180, **kwargs)
        if code and str(code) == "200":
            rs = json.loads(response)
        else:
            rs = {
                "code": code,
                "message": response,
                "data": []
            }
        logger.info(f"send_sync_post_request, cost time: {str(time.time() - start)}")
    except Exception as e:
        logger.error(f"send_sync_post_request, error: {traceback.format_exc()}")
        rs = {
            "code": "500",
            "message": traceback.format_exc(),
            "data": []
        }
    finally:
        logger.info(f'send_sync_post_request, req_url: {req_url}, req_params: {req_params}, rs: {rs}')
        return rs


def check_recv_params(recv_params, cls):
    flag, resp = True, get_resp()
    try:
        cls_fields = list(cls.__dict__.get('__annotations__', {}).keys())
        for recv_filed in list(recv_params.keys()):
            if recv_filed not in cls_fields:
                flag = False
                resp = {"code": 5480001, "message": f'Unknow field {recv_filed}, please check!'}
                logger.info(f'check_recv_params fail, recv_params: {recv_params}, resp: {resp}')
                break
    except Exception:
        logger.error('check_recv_params, error: %s', traceback.format_exc())
        resp["code"] = 5480001
        resp["message"] = "check_recv_params, exception"
    finally:
        return flag, resp

def generate_unique_identification():
    return str(uuid.uuid4()).replace('-', '')
