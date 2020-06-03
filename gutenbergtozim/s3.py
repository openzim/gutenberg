#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import os
import zipfile

from kiwixstorage import KiwixStorage
from pif import get_public_ip
from . import logger

def s3_credentials_ok(s3_url_with_credentials):
    logger.info("testing S3 Optimization Cache credentials")
    s3_storage = KiwixStorage(s3_url_with_credentials)
    if not s3_storage.check_credentials(
        list_buckets=True, bucket=True, write=True, read=True, failsafe=True
    ):
        logger.error("S3 cache connection error testing permissions.")
        logger.error(f"  Server: {s3_storage.url.netloc}")
        logger.error(f"  Bucket: {s3_storage.bucket_name}")
        logger.error(f"  Key ID: {s3_storage.params.get('keyid')}")
        logger.error(f"  Public IP: {get_public_ip()}")
        return False
    return s3_storage

def download_from_cache(key, fpath, s3_storage):
    """ whether it successfully downloaded from cache """
    if not s3_storage.has_object(key, s3_storage.bucket_name):
        return False
    fpath.parent.mkdir(parents=True, exist_ok=True)
    try:
        s3_storage.download_file(key, fpath)
    except Exception as exc:
        logger.error(f"{key} failed to download from cache: {exc}")
        return False
    logger.info(f"downloaded {fpath} from cache at {key}")
    return True

def upload_to_cache(asset, format=None, s3_storage=None, book_id=None):
    """ whether it successfully uploaded to cache """
    fpath = asset
    key = f"{book_id}/{format}"
    if isinstance(asset, list):
        with zipfile.ZipFile('temp.zip', 'w') as zipfl:
            for fl in asset:
                zipfl.write(fl)
                fpath = "temp.zip"
    try:
        s3_storage.upload_file(
            fpath, key
        )
    except Exception as exc:
        logger.error(f"{key} failed to upload to cache: {exc}")
        return False
    finally:
        os.unlink("temp.zip")
    logger.info(f"uploaded {fpath} to cache at {key}")
    return True