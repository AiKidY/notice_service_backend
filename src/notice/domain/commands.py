#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
from dataclasses import dataclass
from typing import List, Optional, Dict


class Command():
    pass


@dataclass
class Ping(Command):
    must_list = ["cmd"]
    cmd: str = ''


@dataclass
class SendSMS(Command):
    must_list = ['usernumber', 'content']
    usernumber: str = ''
    content: str = ''
    SignName: str = ''
    TemplateCode: str = ''


@dataclass
class SendMail(Command):
    must_list = ["mail_classify", "sender", "receivers", "subject", "mail_text"]
    mail_classify: str = ''
    authorize_code: str = ''
    sender: str = ''
    receivers: List = None
    carbon_cper: List = None
    bcarbn_cper: List = None
    subject: str = ''
    mail_type: str = ''
    mail_text: str = ''
    mail_attachments: List = None
