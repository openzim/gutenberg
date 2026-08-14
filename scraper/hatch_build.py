from pathlib import Path

from hatchling.metadata.plugin.interface import (  # pyright: ignore[reportMissingImports]
    MetadataHookInterface,
)


class CustomMetadataHook(MetadataHookInterface):
    """Use the repository README as the package long description."""

    def update(self, metadata: dict) -> None:
        metadata["readme"] = {
            "text": (Path(self.root).parent / "README.md").read_text(encoding="utf-8"),
            "content-type": "text/markdown",
        }
