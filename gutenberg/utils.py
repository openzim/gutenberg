#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging

import envoy

logger = logging.getLogger(__name__)


def exec_cmd(cmd):
    return envoy.run(str(cmd))
