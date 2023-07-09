#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import abc
from src.seedwork.infrastructure.repository import ROMRepository
from src.notice.domain.model.noticerecords import NoticeRecords

class NoticeRecordsAbstractRepository(abc.ABC):
    def __init__(self):
        pass

# -----------------------------------------------------------------
class MotorNoticeRecordsAbstractRepository(NoticeRecordsAbstractRepository, ROMRepository):
    def __init__(self, session):
        super().__init__()
        ROMRepository.__init__(self, session, NoticeRecords)
