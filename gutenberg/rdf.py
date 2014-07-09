#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import os

from path import path

from gutenberg import logger
from gutenberg.utils import exec_cmd


def setup_rdf_folder(rdf_url, rdf_path):
    """ Download and Extract rdf-files """

    rdf_tarball = download_rdf_file(rdf_url)
    extract_rdf_files(rdf_tarball, rdf_path)


def download_rdf_file(rdf_url):
    fname = 'rdf-files.tar.bz2'

    if path(fname).exists():
        logger.info("\rdf-files.tar.bz2 already exists in {}".format(fname))
        return fname

    logger.info("\tDownloading {} into {}".format(rdf_url, fname))

    cmd = "wget -O {fname} -c {url}".format(fname=fname, url=rdf_url)
    exec_cmd(cmd)

    return fname


def extract_rdf_files(rdf_tarball, rdf_path):
    if path(rdf_path).exists():
        logger.info("\RDF files already exists in {}".format(rdf_path))
        return

    logger.info("\tExtracting {} into {}".format(rdf_tarball, rdf_path))

    # create destdir if not exists
    dest = path(rdf_path)
    dest.mkdir()

    cmd = "tar -C {dest} --strip-components 2 -x -f {tarb}".format(
        dest=rdf_path, tarb=rdf_tarball)
    exec_cmd(cmd)
    return


def parse_and_fill(rdf_path):
    logger.info("\tLooping throught RDF files in {}".format(rdf_path))

    for root, dirs, files in os.walk(rdf_path):
        if root.endswith('999999'):
            continue

        for fname in files:
            if fname in ('.', '..'):
                continue

            if not fname.endswith('.rdf'):
                continue

            fpath = os.path.join(root, fname)
            parse_and_process_file(fpath)


def parse_and_process_file(rdf_file):
    logger.info("\tParsing file {}".format(rdf_file))
    if not path(rdf_file).exists():
        raise ValueError(rdf_file)
