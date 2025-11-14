import logging
import subprocess
import shutil
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class BuildVueUIHook(BuildHookInterface):
    """Build hook to compile Vue.js UI before packaging."""

    def initialize(self, version, build_data):
        ui_dir = Path(self.root).parent / "ui"
        ui_dist = ui_dir / "dist"

        # Check if UI dist already exists and is up to date
        if ui_dist.exists() and self._is_ui_built(ui_dir, ui_dist):
            logger.info("Vue.js UI is already built, skipping build step")
            return

        if not ui_dir.exists():
            logger.warning(f"UI directory not found at {ui_dir}, skipping Vue.js build")
            return

        logger.info("Building Vue.js UI...")

        # Check if node_modules exists, if not install dependencies
        node_modules = ui_dir / "node_modules"
        if not node_modules.exists():
            logger.info("Installing Vue.js dependencies...")
            # Try npm first, fallback to yarn
            if shutil.which("npm"):
                subprocess.run(
                    ["npm", "install"],
                    cwd=ui_dir,
                    check=True,
                )
            elif shutil.which("yarn"):
                subprocess.run(
                    ["yarn", "install", "--frozen-lockfile"],
                    cwd=ui_dir,
                    check=True,
                )
            else:
                logger.warning(
                    "Neither npm nor yarn found. Vue.js UI will not be built. "
                    "Please install dependencies manually."
                )
                return

        # Build Vue.js app
        if shutil.which("npm"):
            subprocess.run(
                ["npm", "run", "build"],
                cwd=ui_dir,
                check=True,
            )
        elif shutil.which("yarn"):
            subprocess.run(
                ["yarn", "build"],
                cwd=ui_dir,
                check=True,
            )
        else:
            logger.warning("Neither npm nor yarn found. Cannot build Vue.js UI.")
            return

        logger.info("Vue.js UI build completed successfully")
        return super().initialize(version, build_data)

    def _is_ui_built(self, ui_dir: Path, ui_dist: Path) -> bool:
        """Check if UI is already built and up to date."""
        # Check if dist/index.html exists
        index_html = ui_dist / "index.html"
        if not index_html.exists():
            return False

        # Check if package.json is newer than dist (simple heuristic)
        package_json = ui_dir / "package.json"
        if package_json.exists():
            package_mtime = package_json.stat().st_mtime
            dist_mtime = ui_dist.stat().st_mtime
            if package_mtime > dist_mtime:
                return False

        return True
