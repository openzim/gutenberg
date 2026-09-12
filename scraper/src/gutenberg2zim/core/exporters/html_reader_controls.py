"""Export the reader controls shared by HTML-capable sources."""

from importlib import resources

from gutenberg2zim.constants import logger
from gutenberg2zim.core.zim_assembler import ZimAssembler

_READER_CONTROL_ASSETS = (
    ("css/html-reader-controls.css", "text/css"),
    ("js/html-reader-controls.js", "text/javascript"),
    ("icons/info.svg", "image/svg+xml"),
    ("icons/epub.svg", "image/svg+xml"),
    ("icons/pdf.svg", "image/svg+xml"),
    ("icons/scroll-up.svg", "image/svg+xml"),
)


def export_html_reader_control_assets(assembler: ZimAssembler) -> None:
    """Export shared HTML reader controls and icons to the ZIM."""
    assets_dir = resources.files("gutenberg2zim.core") / "assets"

    for zim_path, mimetype in _READER_CONTROL_ASSETS:
        resource = assets_dir.joinpath(*zim_path.split("/"))
        if not resource.is_file():
            raise FileNotFoundError(f"HTML reader control asset not found: {resource}")
        logger.debug(f"Adding {zim_path} to ZIM")
        assembler.add_item_for(
            path=zim_path,
            content=resource.read_bytes(),
            mimetype=mimetype,
            is_front=False,
        )
