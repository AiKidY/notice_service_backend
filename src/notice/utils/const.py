#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from src.notice.service_layer.sms_handler import SMS
from src.notice.service_layer.mail_handler import Mail

module_map = {
    '短信通知模块': SMS().consume,
    '邮件通知模块': Mail().consume
}

api_func_map = {
    'sms': SMS().notice,
    'mail': Mail().notice
}
