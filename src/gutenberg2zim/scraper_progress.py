import json
import threading
from math import ceil

from schedule import every, run_pending

from gutenberg2zim.constants import logger


class ScraperProgress:
    """Helper class to computer scraper progress"""

    def __init__(self, stats_filename: str | None):
        self._lock = threading.Lock()
        self._total = 1
        self._progress = 0
        self._stats_filename = stats_filename

        if self._stats_filename:
            self.report_progress()
            # set a timer to report progress only every 10 seconds,
            # no need to do it more often
            every(10).seconds.do(self.report_progress)

    def increase_total(self, increment: int):
        with self._lock:
            self._total += increment
            run_pending()

    def increase_progress(self, increment: int = 1):
        with self._lock:
            self._progress += increment
            run_pending()

    def report_progress(self):
        if not self._stats_filename:
            return
        logger.info(
            f"Progress: {self._progress}/{self._total} "
            f"({ceil(self._progress*1000/self._total)/10}%)"
        )
        progress = {
            "done": self._progress,
            "total": self._total,
        }
        with open(self._stats_filename, "w") as outfile:
            json.dump(progress, outfile, indent=2)
