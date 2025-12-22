from pathlib import Path
from typing import Any

import i18n

from gutenberg2zim.constants import LOCALES_LOCATION, logger


def setup_i18n() -> None:
    """Configure python-i18n"""
    i18n.set("locale", "en")  # pyright: ignore[reportUnknownMemberType]
    i18n.set("fallback", None)  # pyright: ignore[reportUnknownMemberType]
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
    i18n.set("fallback", "en")  # pyright: ignore[reportUnknownMemberType]


def t(key: str, fallback: str | None = None, **kwargs: Any) -> str:
    """Get translated string"""
    return (
        i18n.t(  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
            key, **kwargs
        )
        if not fallback or has_strict_translation(key)
        else fallback
    )


def has_strict_translation(key: str) -> bool:
    return i18n.translations.has(key, i18n.get("locale"))
