#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import uuid

UUID = uuid.UUID
UUID.v4 = uuid.uuid4


class Currency(int):
    pass
