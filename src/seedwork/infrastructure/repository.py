import logging
import time
import traceback
from typing import List

import sqlalchemy
from bson.objectid import ObjectId
from lycium.modelutils import model_columns

from src.seedwork.application.exceptions import EntityNotFoundException
from src.seedwork.domain.entities import Entity
from src.seedwork.utils import PgOpError

logger = logging.getLogger(__name__)


class Repository:
    pass


class InMemoryRepository(Repository):
    def __init__(self) -> None:
        self.objects = {}

    def get_by_id(self, id) -> Entity:
        try:
            return self.objects[id]
        except KeyError:
            raise EntityNotFoundException

    def insert(self, entity: Entity):
        assert issubclass(entity.__class__, Entity)
        self.objects[entity.id] = entity

    def update(self, entity: Entity):
        assert issubclass(entity.__class__, Entity)
        self.objects[entity.id] = entity

    def delete(self, entity_id):
        del self.objects[entity_id]


class ROMRepository(object):

    def __init__(self, session, table_name):
        self.session = session
        self.table_name = table_name

    def _check_default_fields(self, record):
        default_values = {
            "created_at": int(time.time() * 1000),
            "updated_at": int(time.time() * 1000),
            "sort_value": 1,
            "created_by": "",
            "updated_by": "",
            "obsoleted": False
        }
        for k, v in default_values.items():
            if k not in record:
                record[k] = v
        return record

    async def query_record(self, filters, return_dict=False):
        record = []
        try:
            record = await self.session.find_item(self.table_name, filters)
            if record and return_dict:
                record_dict = {}
                for k in record._sa_class_manager._all_key_set:
                    record_dict[k] = getattr(record, k)
                return record_dict
        except Exception:
            logger.error(f'ROMRepository, query_record, error: {traceback.format_exc()}')
        return record

    async def query_records_list(self, filters, limit=10, offset=0, sort=None, direction=None,
                                 selections=None, joins=None, outerjoins=None):
        records, count = [], 0
        try:
            records, count = await self.session.query_list(self.table_name, filters, limit, offset,
                                                           sort, direction, selections=selections,
                                                           joins=joins, outerjoins=outerjoins, skipfields={})
        except Exception:
            logger.error(f'ROMRepository, query_records_list, error: {traceback.format_exc()}')
        return records, count

    async def query_records(self, filters, sort=None, direction='asc', joins=None):
        records = []
        try:
            records = await self.session.query_all(self.table_name, filters, sort, direction, joins)
        except Exception:
            logger.error(f'ROMRepository, query_records, error: {traceback.format_exc()}')
        return records

    async def query_count(self, filters):
        count = None
        try:
            count = await self.session.get_count(self.table_name, filters)
        except Exception:
            logger.error(f'ROMRepository, query_count, error: {traceback.format_exc()}')
        return count

    async def insert_one(self, record):
        try:
            model = record.__class__
            columns, pk = model_columns(model)
            dbinstance = self.session.get_model_dbinstance(model)
            async with dbinstance.engine.begin() as conn:
                values, defaults = self.session.get_rdbms_instance_insert_values(record, model, columns, pk)
                if not values:
                    return False
                stmt = sqlalchemy.insert(model).values(**values)
                await conn.execute(stmt)
                await conn.commit()
        except Exception:
            logger.error(f'ROMRepository, insert_one, error: {traceback.format_exc()}')
        return record

    async def insert_many(self, records: list):
        try:
            model = records[0].__class__
            columns, pk = model_columns(model)
            dbinstance = self.session.get_model_dbinstance(model)
            async with dbinstance.engine.begin() as conn:
                for item in records:
                    values, defaults = self.session.get_rdbms_instance_insert_values(item, model, columns, pk)
                    if not values:
                        return False
                    stmt = sqlalchemy.insert(model).values(**values)
                    await conn.execute(stmt)
                await conn.commit()
        except Exception:
            logger.error(f'ROMRepository, insert_many, error: {traceback.format_exc()}')
        return records

    async def update(self, filters, values: dict):
        flag = False
        try:
            dbinstance = self.session.get_model_dbinstance(self.table_name)
            async with dbinstance.engine.begin() as conn:
                stmt = sqlalchemy.update(self.table_name).filter(*filters).values(**values)
                await conn.execute(stmt)
                await conn.commit()
                flag = True
        except Exception:
            logger.error(f'ROMRepository, update, error: {traceback.format_exc()}')
        return flag

    async def delete(self, filters):
        deleted_count = None
        try:
            dbinstance = self.session.get_model_dbinstance(self.table_name)
            async with dbinstance.engine.begin() as conn:
                stmt = sqlalchemy.delete(self.table_name).filter(*filters)
                cursor = await conn.execute(stmt)
                await conn.commit()
                deleted_count = cursor.rowcount
        except Exception:
            logger.error(f'ROMRepository, delete, error: {traceback.format_exc()}')
        return deleted_count

    async def exec_sql(self, db_category, sql):
        res = []
        try:
            logger.info("ROMRepository, exec_sql: %s", sql)
            rows = await self.session.exec_query(db_category, sql)
            res = [dict(row._mapping) for row in rows]
        except Exception:
            logger.error(f'ROMRepository, exec_sql, error: {traceback.format_exc()}')
        return res

    def _convert_to_str(self, m):
        if m:
            for k in m:
                if isinstance(m[k], ObjectId):
                    m[k] = str(m[k])
        return m


class SQLRepository(object):
    """
    直接执行sql的, 不建议使用
    """

    def __init__(self, session, table_name):
        self.session = session
        self.table_name = table_name

    async def execute_sql(self, db_category, sql):
        # db_category, sql,
        rows = await self.session.exec_query(db_category, sql)
        return rows


class RedisCacheRepository(object):
    def __init__(self, cache_proxy):
        self.cache_proxy = cache_proxy

    async def get_hospital_by_code(self, hosp_info: str, keys: list = ['id', "name", "code"]):
        hosp_obj = await self.cache_proxy.getObject(hosp_info, keys)
        if not hosp_obj:
            return None
        return hosp_obj

    async def get_person_by_jobcode(self, person_info: str, keys: List[str]):
        per_obj = await self.cache_proxy.getObject(person_info, keys)
        if not per_obj:
            return None
        return per_obj
