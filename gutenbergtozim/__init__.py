#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import logging
import threading
from pathlib import Path as path

from zimscraperlib.logging import getLogger

logger = getLogger(__name__, level=logging.DEBUG)

TMP_FOLDER = "tmp"
TMP_FOLDER_PATH = path(TMP_FOLDER)

VERSION = "1.1.9"

lock = threading.Lock()

creator = None
