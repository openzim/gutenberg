import pathlib
import threading
from datetime import date
from typing import Any, Optional, Tuple, Union

from zimscraperlib.zim.creator import Creator

from gutenbergtozim import VERSION, logger


class Global:
    """Shared context accross all scraper components"""

    creator = None
    _lock = threading.Lock()

    total = 0
    progress = 0

    @staticmethod
    def set_total(total):
        with Global._lock:
            Global.total = total

    @staticmethod
    def reset_progress():
        with Global._lock:
            Global.progress = 0

    @staticmethod
    def inc_progress():
        with Global._lock:
            Global.progress += 1

    @staticmethod
    def setup(filename, language, title, description, name):

        Global.creator = Creator(
            filename=filename,
            main_path="Home.html",
            favicon_path="illustration",
            language=language,
            workaround_nocancel=False,
            title=title,
            description=description,
            creator="gutenberg.org",
            publisher="Kiwix",
            name=name,
            tags="_category:gutenberg;gutenberg",
            scraper="gutengergtozim-{v}".format(v=VERSION),
            date=date.today(),
        ).config_verbose(True)

    @staticmethod
    def add_item_for(
        path: str,
        title: Optional[str] = None,
        fpath: Optional[pathlib.Path] = None,
        content: Optional[bytes] = None,
        mimetype: Optional[str] = None,
        is_front: Optional[bool] = None,
        should_compress: Optional[bool] = None,
        delete_fpath: Optional[bool] = False,
        callback: Optional[Union[callable, Tuple[callable, Any]]] = None,
    ):

        logger.debug("\t\tAdding ZIM item at {}".format(path))
        with Global._lock:
            Global.creator.add_item_for(
                path=path,
                title=title,
                fpath=fpath,
                content=content,
                mimetype=mimetype,
                is_front=is_front,
                should_compress=should_compress,
                delete_fpath=delete_fpath,
                callback=callback,
            )

    @staticmethod
    def add_illustration(illus_fpath, illus_size):
        with open(illus_fpath, "rb") as fh:
            with Global._lock:
                Global.creator.add_illustration(illus_size, fh.read())

    @staticmethod
    def start():
        Global.creator.start()

    @staticmethod
    def finish():
        if Global.creator.can_finish:
            logger.info("Finishing ZIM file")
            with Global._lock:
                Global.creator.finish()
            logger.info(
                f"Finished Zim {Global.creator.filename.name} "
                f"in {Global.creator.filename.parent}"
            )
