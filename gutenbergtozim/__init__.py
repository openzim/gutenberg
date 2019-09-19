#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
from logging.config import dictConfig


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'iso8601': {
            'handlers': ['null'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'peewee': {
            'handlers': ['null'],
            'level': 'DEBUG',
            'propagate': False,
        },
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        }
    }
}

dictConfig(LOGGING)

logger = logging.getLogger(__name__)

TMP_FOLDER = 'tmp'

VERSION = "1.1.4"
