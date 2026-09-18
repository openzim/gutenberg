"""Tests for the reader controls shared by HTML-capable sources."""

from importlib import resources
from unittest.mock import MagicMock

from gutenberg2zim.core.exporters.html_reader_controls import (
    export_html_reader_control_assets,
)
from gutenberg2zim.core.models import Work
from gutenberg2zim.sources.gutenberg.rewriter import update_html_for_static


def test_exports_bundled_reader_control_assets_with_zim_paths_and_media_types():
    assembler = MagicMock(name="assembler")

    export_html_reader_control_assets(assembler)

    calls = assembler.add_item_for.call_args_list
    expected_assets = [
        ("css/html-reader-controls.css", "text/css"),
        ("js/html-reader-controls.js", "text/javascript"),
        ("icons/info.svg", "image/svg+xml"),
        ("icons/epub.svg", "image/svg+xml"),
        ("icons/pdf.svg", "image/svg+xml"),
        ("icons/scroll-up.svg", "image/svg+xml"),
    ]
    actual_assets = [(call.kwargs["path"], call.kwargs["mimetype"]) for call in calls]
    assert actual_assets == expected_assets
    assets_dir = resources.files("gutenberg2zim.core") / "assets"
    for call in calls:
        zim_path = call.kwargs["path"]
        resource = assets_dir.joinpath(*zim_path.split("/"))
        assert call.kwargs["content"] == resource.read_bytes()
        assert call.kwargs["is_front"] is False


def test_gutenberg_reader_controls_keep_root_relative_asset_paths():
    work = Work(id="10", source="gutenberg", title="A Book")

    html = update_html_for_static(
        work,
        "<!doctype html><html><head></head><body><p>Text</p></body></html>",
        ["epub", "pdf"],
    )

    controls = html.find(id="html-reader-controls")
    assert controls is not None
    assert html.find("link", href="css/html-reader-controls.css") is not None
    assert html.find("script", src="js/html-reader-controls.js") is not None
    assert [str(image["src"]) for image in controls.find_all("img")] == [
        "icons/info.svg",
        "icons/epub.svg",
        "icons/pdf.svg",
        "icons/scroll-up.svg",
    ]
