import zipfile
from pathlib import Path

from kiwixstorage import KiwixStorage
from pif import get_public_ip

from gutenberg2zim.constants import TMP_FOLDER, logger
from gutenberg2zim.database import Book
from gutenberg2zim.utils import archive_name_for


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


def download_from_cache(
    book: Book,
    etag: str | None,
    book_format: str,
    dest_dir: Path,
    s3_storage: KiwixStorage,
    optimizer_version: dict[str, str] | None,
) -> bool:
    """whether it successfully downloaded from cache"""
    key = f"{book.book_id}/{book_format}"
    if not s3_storage.has_object(key):
        return False
    meta = s3_storage.get_object_stat(key).meta
    if meta.get("etag") != etag:  # type: ignore
        logger.error(
            f"etag doesn't match for {key}. "
            f"Expected {etag}, got {meta.get('etag')}"  # type: ignore
        )
        return False
    if optimizer_version is not None and (
        meta.get("optimizer_version") != optimizer_version[book_format]  # type: ignore
    ):
        logger.error(
            f"optimizer version doesn't match for {key}. Expected "
            "{optimizer_version[book_format]}, got {meta.get('optimizer_version')}"
        )
        return False
    dest_dir.mkdir(parents=True, exist_ok=True)
    if book_format == "cover":
        fpath = dest_dir / f"{book.book_id}_cover_image.jpg"
    else:
        if book_format == "html":
            book_format = "zip"
        fpath = dest_dir / archive_name_for(book, book_format)
    try:
        s3_storage.download_file(key, fpath)
        if book_format == "zip":
            with zipfile.ZipFile(fpath, "r") as zipfl:
                zipfl.extractall(dest_dir)
            fpath.unlink(missing_ok=True)
    except Exception as exc:
        logger.error(f"{key} failed to download from cache: {exc}")
        return False
    logger.info(f"downloaded {fpath} from cache at {key}")
    return True


def upload_to_cache(book_id, asset, etag, book_format, s3_storage, optimizer_version):
    """whether it successfully uploaded to cache"""
    fpath = asset
    key = f"{book_id}/{book_format}"
    zippath = Path(f"{TMP_FOLDER}/{book_id}.zip")
    if isinstance(asset, list):
        with zipfile.ZipFile(zippath, "w") as zipfl:
            for fl in asset:
                if fl.exists():
                    zipfl.write(fl, arcname=fl.name)
                else:
                    logger.error(f"Skipping {fl.name} in S3 zip as it may be corrupt")
        fpath = zippath
    try:
        s3_storage.upload_file(
            fpath,
            key,
            meta={"etag": etag, "optimizer_version": optimizer_version[book_format]},
        )
    except Exception as exc:
        logger.error(f"{key} failed to upload to cache: {exc}")
        return False
    finally:
        zippath.unlink(missing_ok=True)
    logger.info(f"uploaded {fpath} to cache at {key}")
    return True
