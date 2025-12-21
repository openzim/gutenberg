from pathlib import Path
from typing import Any

import i18n

from gutenberg2zim.constants import LOCALES_LOCATION, logger


def _ensure_fallback() -> None:
    """Ensure fallback is always set (python-i18n may lose it in some contexts)"""
    if not i18n.get("fallback"):  # pyright: ignore[reportUnknownMemberType]
        i18n.set("fallback", "en")  # pyright: ignore[reportUnknownMemberType]


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
    _ensure_fallback()


def t(key: str, fallback: str | None = None, **kwargs: Any) -> str:
    """Get translated string"""
    _ensure_fallback()

    result = i18n.t(
        key, **kwargs
    )  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

    # If python-i18n's fallback didn't work and we have a manual fallback, use it
    if result == key and fallback is not None:
        return fallback

    return result


def has_strict_translation(key: str) -> bool:
    return i18n.translations.has(key, i18n.get("locale"))
