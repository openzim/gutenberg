import threading
from pathlib import Path
from typing import Any

import i18n
from i18n import resource_loader

from gutenberg2zim.constants import LOCALES_LOCATION, logger

# Thread lock for locale switching to prevent race conditions
# when t() is called from multiple threads (e.g., via multiprocessing.dummy.Pool)
_locale_lock = threading.Lock()


def setup_i18n() -> None:
    """Configure python-i18n"""
    i18n.set("locale", "en")  # pyright: ignore[reportUnknownMemberType]
    i18n.set("fallback", "en")  # pyright: ignore[reportUnknownMemberType]
    i18n.set("file_format", "json")  # pyright: ignore[reportUnknownMemberType]
    i18n.set(  # pyright: ignore[reportUnknownMemberType]
        "filename_format", "{locale}.{format}"
    )
    i18n.set("skip_locale_root_data", True)  # pyright: ignore[reportUnknownMemberType]

    locales_location = Path(LOCALES_LOCATION)
    if not locales_location.exists():
        raise Exception(f"Missing locales folder '{locales_location}'")
    logger.info(f"Loading locales from {locales_location}")
    i18n.load_path.append(locales_location)  # pyright: ignore


def change_locale(lang: str) -> None:
    """Change locale"""
    i18n.set("locale", lang)  # pyright: ignore[reportUnknownMemberType]


def t(key: str, fallback: str | None = None, **kwargs: Any) -> str:
    """Get translated string with manual fallback support"""
    current_locale = i18n.get("locale")  # pyright: ignore[reportUnknownMemberType]
    fallback_locale = (
        i18n.get("fallback") or "en"
    )  # pyright: ignore[reportUnknownMemberType]

    result = i18n.t(
        key, **kwargs
    )  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

    # python-i18n's fallback doesn't work in our context (fallback becomes None)
    if result == key and current_locale != fallback_locale:
        with _locale_lock:
            try:
                i18n.set(
                    "locale", fallback_locale
                )  # pyright: ignore[reportUnknownMemberType]
                resource_loader.search_translation(key, fallback_locale)
                fallback_result = i18n.t(
                    key, **kwargs
                )  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                if fallback_result != key:
                    result = fallback_result
            except (AttributeError, KeyError, ImportError) as e:
                logger.debug(f"Manual fallback failed for key '{key}': {e}")
            finally:
                i18n.set(
                    "locale", current_locale
                )  # pyright: ignore[reportUnknownMemberType]

    if result != key:
        return result
    return fallback if fallback is not None else key
