#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import abc
from lycium.dbproxy import DbProxy
from src.notice.adapters import repository


class AbstractUnitOfWork(abc.ABC):
    notice_records: repository.NoticeRecordsAbstractRepository

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.rollback()

    def commit(self):
        return self.commit()

    async def acommit(self):
        await self._acommit()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.arollback()

    def collect_new_events(self):
        return []

    @abc.abstractmethod
    def _commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def _acommit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError

    @abc.abstractmethod
    def arollback(self):
        raise NotImplementedError


class MotorUnitOfWork(AbstractUnitOfWork):

    def __init__(self):
        self.commit_success = False
        self.db_proxy = DbProxy()

    async def __aenter__(self):
        self.commit_success = False
        self.notice_records = repository.MotorNoticeRecordsAbstractRepository(self.db_proxy)
        return self

    async def __aexit__(self, *args):
        await super().__aexit__(*args)

    async def _acommit(self):
        pass

    async def arollback(self):
        pass

    def _commit(self):
        pass

    def rollback(self):
        pass
