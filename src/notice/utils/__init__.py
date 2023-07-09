#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import json
import time
import base64
import datetime
import logging
import traceback
from datetime import date, datetime
from bson import ObjectId

logger = logging.getLogger(__name__)


def get_cur_time(type='date'):
    cur_time = None
    try:
        if type == 'date':
            cur_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        elif type == 'timestamp':
            cur_time = int(time.time() * 1000)
    except Exception as e:
        logger.error(f'get_cur_time, error: {traceback.format_exc()}')
    finally:
        return cur_time


def timestamp_to_date(date_timestamp):
    dt = ""
    try:
        time_local = time.localtime(date_timestamp / 1000)
        # 转换成新的时间格式(精确到秒)
        dt = time.strftime("%Y-%m-%d", time_local)
    except Exception as e:
        logger.error(f'timestamp_to_date, error: {e}')
    finally:
        return dt


def get_cur_hour():
    cur_hour = -1
    try:
        cur_hour = datetime.datetime.now().hour
    except Exception as e:
        logger.error(f'get_cur_hour, error: {e}')
    finally:
        return int(cur_hour)


def get_day_appoint_timestamp(hms='00:00:00'):
    date_timestamp = 0
    try:
        cur_date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        date_timestamp = time.mktime(time.strptime(str(cur_date) + " " + str(hms), "%Y-%m-%d %H:%M:%S")) * 1000
    except Exception as e:
        logger.error(f'get_day_timestamp, error: {e}')
    finally:
        return date_timestamp


def cal_pre_aft_date(date_str, number, type='pre'):
    cal_date = date_str
    try:
        dt = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        if type == 'pre':
            cal_date = dt - datetime.timedelta(days=number)
        elif type == 'aft':
            cal_date = dt + datetime.timedelta(days=number)
    except Exception as e:
        logger.error(f'cal_pre_aft_date, date_str: {date_str}, number: {number}, error: {e}')
    finally:
        logger.info(f'cal_pre_aft_date, date_str: {date_str}, number: {number}, type: {type}, cal_date: {cal_date}')
        return str(cal_date)


def data_desensitization(string, type):
    try:
        # 身份证脱敏
        if type == 'id_number':
            old = string[2: -4]
            if len(string) < 6:
                old = string[1:]

            new = '*' * len(old)
            string = string.replace(old, new)
        # 姓名脱敏
        elif type == 'name':
            if len(string) < 2:
                pass
            elif len(string) == 2:
                string = string[0] + '*'
            else:
                string = string[0] + '*' * (len(string) - 2) + string[len(string) - 1]
        # 电话脱敏
        elif type == 'contact':
            old = string[3: 7]
            new = '*' * len(old)
            string = string.replace(old, new)
    except Exception as e:
        logger.error(f'data_desensitization, error: {e}')
    finally:
        logger.info(f'data_desensitization, string: {string}, type: {type}')
        return string


def base64_decode(val):
    return base64.b64decode(val).decode()

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