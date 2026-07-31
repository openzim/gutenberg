"""Vue.js UI dist folder exporter (moved from `gutenberg2zim.zim`)."""

import re
from html import escape
from pathlib import Path

from gutenberg2zim.constants import logger
from gutenberg2zim.core.zim_assembler import ZimAssembler


def export_ui_dist(ui_dist: Path, title: str, assembler: ZimAssembler) -> None:
    """Export Vue.js UI dist folder to ZIM file."""
    if not ui_dist.exists():
        raise FileNotFoundError(f"UI dist directory not found: {ui_dist}")

    logger.info(f"Adding Vue.js UI files from {ui_dist}")
    file_count = 0
    for file in ui_dist.rglob("*"):
        if file.is_dir():
            continue
        path = file.relative_to(ui_dist).as_posix()
        logger.debug(f"Adding {path} to ZIM")

        # Update index.html title
        if path == "index.html":
            html_content = file.read_text(encoding="utf-8")
            new_html_content = re.sub(
                r"(<title>)(.*?)(</title>)",
                lambda match: f"{match.group(1)}{escape(title)}{match.group(3)}",
                html_content,
                flags=re.IGNORECASE,
            )
            assembler.add_item_for(
                path=path,
                content=new_html_content,
                mimetype="text/html",
                is_front=True,
            )
        else:
            assembler.add_item_for(
                path=path,
                fpath=file,
                is_front=False,
            )
        file_count += 1
    logger.info(f"Successfully added {file_count} UI files to ZIM")
