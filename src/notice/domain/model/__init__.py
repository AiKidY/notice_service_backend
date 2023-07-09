#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time

from sqlalchemy import Column, String, BigInteger, Boolean
from sqlalchemy.ext.declarative import declarative_base

ModelBase = declarative_base()


class ModifyingBehevior(object):
    """
    模型固定字段
    """
    obsoleted = Column('obsoleted', Boolean, default=False)
    created_at = Column('created_at', BigInteger, default=lambda: int(time.time() * 1000))
    updated_at = Column('updated_at', BigInteger, default=lambda: int(time.time() * 1000),
                        onupdate=lambda: int(time.time() * 1000))
    created_by = Column('created_by', String(50))
    updated_by = Column('updated_by', String(50))
