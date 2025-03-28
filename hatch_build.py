import logging
import subprocess
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# update list in constants.py as well
JS_DEPS = [
    "datatables/datatables.min.css",
    "datatables/datatables.min.js",
    "jquery/jquery-1.11.1.min.js",
]


class GetJsDepsHook(BuildHookInterface):
    def initialize(self, version, build_data):
        if self.deps_already_installed():
            logger.info("JS dependencies are already installed, skipping it")
            return
        subprocess.run(
            str(Path(self.root).joinpath("get_js_deps.sh")),
            check=True,
        )
        return super().initialize(version, build_data)

    def deps_already_installed(self) -> bool:
        for dep in JS_DEPS:
            if (
                not Path(self.root)
                .joinpath("gutenberg2zim/templates")
                .joinpath(dep)
                .exists()
            ):
                return False
        return True
