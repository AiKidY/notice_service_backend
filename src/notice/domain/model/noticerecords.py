#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, Boolean

from src.notice.adapters.const import ModelName
from src.notice.domain.model import ModelBase, ModifyingBehevior


class NoticeRecords(ModelBase, ModifyingBehevior):
    """
    通知记录表
    """
    __tablename__ = ModelName.NoticeRecords.value

    id = Column('id', String(50), primary_key=True)
    notice_type = Column('notice_type', String(10))
    status = Column('status', Boolean())
    status_msg = Column('status_msg', String(500))
