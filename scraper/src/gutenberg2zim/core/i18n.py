from pathlib import Path
from typing import Any

import i18n

from gutenberg2zim.constants import LOCALES_LOCATION, logger


def setup_i18n(source_namespace: str) -> None:
    """Configure python-i18n"""
    i18n.set(  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
        "locale", "en"
    )
    i18n.set(  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
        "fallback", None
    )
    i18n.set(  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
        "file_format", "json"
    )
    i18n.set(  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
        "filename_format", "{locale}.{format}"
    )
    i18n.set(  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
        "skip_locale_root_data", True
    )

    locales_location = Path(LOCALES_LOCATION)
    if not locales_location.exists():
        raise Exception(f"Missing locales folder '{locales_location}'")

    logger.info(
        "Loading locales from %s with source namespace %s",
        locales_location,
        source_namespace,
    )
    i18n.resource_loader.unload_everything()  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
    i18n.load_path.clear()  # pyright: ignore
    i18n.load_path.append(locales_location)  # pyright: ignore


def change_locale(lang: str) -> None:
    """Change locale"""
    i18n.set(  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
        "locale", lang
    )
    i18n.set(  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
        "fallback", "en"
    )


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
    return i18n.translations.has(  # pyright: ignore[reportAttributeAccessIssue]
        key,
        i18n.get("locale"),  # pyright: ignore[reportAttributeAccessIssue]
    )
