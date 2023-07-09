#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import contextvars

context_request_id = contextvars.ContextVar('Id of request')
