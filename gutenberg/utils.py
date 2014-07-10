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


def download_file(url, fname):
    output = "--output {}".format(fname) if fname else "--remote-name"
    cmd = ("curl --fail --insecure --location {output} --silent "
           "--show-error -C - --url {url}".format(output=output, url=url))
    cmdr = exec_cmd(cmd)
    return cmdr.status_code == 0
