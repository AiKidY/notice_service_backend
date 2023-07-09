#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
from pydantic import BaseModel, Field
from .value_objects import UUID


class Entity(BaseModel):
    pass


class ModelBase(Entity):
    created_at: float = time.time() * 1000
    updated_at: float = time.time() * 1000
    sort_value: int = 1
    created_by: str = ""
    updated_by: str = ""
    obsoleted = False

    def to_dict(self):
        m = {}
        for k in self.__dict__:
            v = self.__dict__[k]
            if not k.startswith("_"):
                m[k] = v
        return m

    def to_dict_filter_invalid_value(self):
        m = {}
        for k in self.__dict__:
            v = self.__dict__[k]
            if not k.startswith("_") and v:
                m[k] = v
        return m
