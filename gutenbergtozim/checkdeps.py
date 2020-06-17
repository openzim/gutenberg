#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import subprocess

from gutenbergtozim import logger


def check_dependencies():
    def bin_is_present(binary):
        try:
            subprocess.Popen(
                binary,
                universal_newlines=True,
                shell=False,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
            )
        except OSError:
            return False
        else:
            return True

    all_bins = {
        "gifsicle": "GIF compression tool, part of `gifsicle` package",
        "pngquant": "PNG compression tool, part of `pngquant` package",
        "advdef": "PNG compression tool, part of `advancecomp` package",
        "jpegoptim": "JPEG compression tool, part of `jpegoptim` package",
        "zip": "ZIP file packager for ePub",
        "tar": "TAR archive extractor",
        "curl": "Files downloader, part of `curl` package",
        "zimwriterfs": "ZIM file writer, available on kiwix-other repository",
    }

    all_good = True
    has_zimwriter = True
    for bin, msg in all_bins.items():
        if bin == "zimwriterfs":
            if not bin_is_present(bin):
                has_zimwriter = False
                continue

        if not bin_is_present(bin):
            logger.error("\t*{}* binary missing. {}".format(bin, msg))
            all_good = False

    return all_good, has_zimwriter
