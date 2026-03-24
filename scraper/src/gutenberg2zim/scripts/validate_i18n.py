#!/usr/bin/env python3
"""Validate i18n translation files and usage in code."""

import json
import re
import sys
from pathlib import Path
from typing import Any

# ruff: noqa: T201


def load_json(path: Path) -> dict[str, Any]:
    """Load and parse a JSON file."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)  # type: ignore
    except json.JSONDecodeError as e:
        print(f"   ❌ Invalid JSON in {path.name}: {e}")
        raise
    except UnicodeDecodeError as e:
        print(f"   ❌ Encoding error in {path.name}: {e}")
        raise


def get_leaf_keys(data: dict[str, Any], prefix: str = "") -> set[str]:
    """Recursively extract all leaf keys (keys with string values) from nested
    dictionary."""
    result: set[str] = set()

    for key, value in data.items():
        if key == "@metadata":
            continue
        full_key = f"{prefix}.{key}" if prefix else key

        if isinstance(value, dict):
            child_result = get_leaf_keys(value, full_key)
            result.update(child_result)
        else:
            result.add(full_key)

    return result


def get_leaf_values(data: dict[str, Any], prefix: str = "") -> dict[str, str]:
    """Recursively extract all leaf key-value pairs from nested dictionary."""
    result: dict[str, str] = {}

    for key, value in data.items():
        if key == "@metadata":
            continue
        full_key = f"{prefix}.{key}" if prefix else key

        if isinstance(value, dict):
            child_result = get_leaf_values(value, full_key)
            result.update(child_result)
        else:
            result[full_key] = str(value)

    return result


def extract_placeholders(text: str) -> set[str]:
    """Extract placeholders like {count}, {name} from translation text."""
    return set(re.findall(r"\{([^}]+)\}", text))


def validate_translation_quality(
    locale_file: Path, en_values: dict[str, str]
) -> list[str]:
    """Check translation quality for a locale file."""
    locale_data = load_json(locale_file)
    return validate_translation_quality_from_data(locale_data, en_values)


def validate_translation_quality_from_data(
    locale_data: dict[str, Any], en_values: dict[str, str]
) -> list[str]:
    """Check translation quality from already-loaded locale data."""
    issues: list[str] = []
    locale_values = get_leaf_values(locale_data)

    for key, en_text in en_values.items():
        if key not in locale_values:
            continue

        locale_text = locale_values[key]

        # Check for empty translations
        if not locale_text.strip():
            issues.append(f"   - {key}: empty translation")
            continue

        # Check placeholder consistency
        en_placeholders = extract_placeholders(en_text)
        locale_placeholders = extract_placeholders(locale_text)

        if en_placeholders != locale_placeholders:
            missing = en_placeholders - locale_placeholders
            extra = locale_placeholders - en_placeholders
            if missing:
                issues.append(f"   - {key}: missing placeholders {missing}")
            if extra:
                issues.append(f"   - {key}: extra placeholders {extra}")

    return issues


def is_valid_key(key: str) -> bool:
    """Check if a key is valid (not dynamic or system-generated)."""
    return (
        "{{" not in key
        and "${" not in key
        and not key.startswith("update:")
        and not key.startswith("go-to-")
        and key not in ["#app", "-", "should pass"]
    )


def extract_keys_from_file(file_path: Path, file_type: str) -> set[str]:
    """Extract i18n keys from files based on type."""
    content = file_path.read_text(encoding="utf-8")

    patterns = {
        "vue": r't\s*\(\s*["\']([^"\']+)["\']',
        "python": r'i18n\.t\s*\(\s*["\']([^"\']+)["\']',
        "html": r'data-l10n-id\s*=\s*["\']([^"\']+)["\']',
    }

    pattern = patterns.get(file_type)
    if not pattern:
        return set()

    found_keys = re.findall(pattern, content)
    return {key for key in found_keys if is_valid_key(key)}


def process_files(
    directory: Path,
    file_patterns: dict[str, str],
    repo_root: Path,
    code_keys: set[str],
    key_locations: dict[str, list[str]],
) -> None:
    """Process files in directory and extract keys."""
    if not directory.exists():
        raise FileNotFoundError(
            f"Directory not found: {directory}. "
            "Validation script is misconfigured or repository structure has changed."
        )

    for pattern, file_type in file_patterns.items():
        for file_path in directory.rglob(pattern):
            if "node_modules" in str(file_path):
                continue
            try:
                if file_path.samefile(Path(__file__)):
                    continue
            except (OSError, ValueError):
                pass

            keys = extract_keys_from_file(file_path, file_type)
            if keys:
                print(
                    f"   Found {len(keys)} keys in {file_path.relative_to(repo_root)}"
                )
                code_keys.update(keys)
                for key in keys:
                    key_locations.setdefault(key, []).append(
                        str(file_path.relative_to(repo_root))
                    )


def get_ignored_keys(locales_dir: Path, en_data: dict[str, Any]) -> set[str]:
    """Get keys that should not trigger 'unused key' warnings.

    These include:
    - Locale metadata fields (e.g., 'language', 'isocode')
      These exist in locale files but are not accessed by application code
    - Dynamic language name keys (e.g., 'languageNames.af', 'languageNames.ar')
      Accessed dynamically via languageNames[code]
    - Dynamic LCC shelf keys (e.g., 'lccShelves.A', 'lccShelves.B')
      Accessed dynamically or reserved for future use
    """
    base_ignored = {
        "language",
        "isocode",
    }

    # Extract language codes from actual locale files
    language_codes = [
        f.stem
        for f in locales_dir.glob("*.json")
        if f.name not in ["en.json", "qqq.json"]
    ]

    # Extract LCC codes from en.json lccShelves section
    lcc_codes = []
    if "lccShelves" in en_data:
        lcc_codes = list(en_data["lccShelves"].keys())

    template_keys = {
        "book.anonymous",
        "book.cover",
        "book.coverLabel",
        "book.downloads",
        "book.fullName",
        "book.licenseCopyright",
        "book.licensePd",
        "book.title",
        "book.various",
        "book.worksAvailable",
        "common.anyCatalog",
        "common.chooseLanguage",
        "common.filterBy",
        "common.mainLanguages",
        "common.navigateTo",
        "common.otherLanguages",
        "common.search",
        "common.sortBy",
        "common.uiLanguage",
        "itemTypes.authors",
        "itemTypes.books",
        "itemTypes.shelves",
        "messages.noAuthors",
        "messages.noBooks",
        "messages.noBooksInShelf",
        "messages.noFormats",
        "messages.noLanguages",
        "messages.noShelves",
        "messages.notFoundShelf",
        "shelf.booksIn",
        "authors.title",
    }

    ignored = base_ignored | template_keys
    ignored.update(f"languageNames.{code}" for code in language_codes)
    ignored.add("languageNames.en")
    ignored.update(f"lccShelves.{code}" for code in lcc_codes)

    return ignored


def main() -> int:
    """Main validation function."""
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent.parent.parent
    locales_dir = repo_root / "locales"
    scraper_src_dir = repo_root / "scraper" / "src"
    ui_src_dir = repo_root / "ui" / "src"

    print("🔍 Validating i18n translations...")
    print()

    errors: list[str] = []

    # Check required directories exist
    print("📂 Checking required directories and files...")
    for path, description in [
        (locales_dir, "locales directory"),
        (scraper_src_dir, "scraper src directory"),
        (ui_src_dir, "ui src directory"),
    ]:
        if not path.exists():
            print(f"   ❌ Missing {description}: {path}")
            return 1
        print(f"   ✅ Found {description}")

    print()

    # Load and validate locale files
    print("📁 Checking locale files...")
    en_path = locales_dir / "en.json"
    qqq_path = locales_dir / "qqq.json"

    for path, name in [(en_path, "en.json"), (qqq_path, "qqq.json")]:
        if not path.exists():
            print(f"   ❌ Missing {name} at {path}")
            return 1

    en_data = load_json(en_path)
    qqq_data = load_json(qqq_path)

    en_keys = get_leaf_keys(en_data)
    qqq_keys = get_leaf_keys(qqq_data)
    en_values = get_leaf_values(en_data)

    print(f"   Found {len(en_keys)} keys in en.json")
    print(f"   Found {len(qqq_keys)} keys in qqq.json")

    # Check en.json and qqq.json key consistency
    if en_keys != qqq_keys:
        missing_in_qqq = en_keys - qqq_keys
        missing_in_en = qqq_keys - en_keys

        if missing_in_qqq:
            errors.append(
                f"❌ {len(missing_in_qqq)} keys missing documentation in qqq.json"
            )
            errors.append(
                "   TranslateWiki requires documentation for all keys in qqq.json"
            )
            for key in sorted(missing_in_qqq):
                errors.append(f"   - {key}")

        if missing_in_en:
            errors.append("❌ Keys in qqq.json but not in en.json!")
            errors.append(f"   Extra in qqq.json: {sorted(missing_in_en)}")
    else:
        print("   ✅ en.json and qqq.json keys match perfectly")

    # Check other locale files
    quality_issues: dict[str, list[str]] = {}

    for locale_file in sorted(locales_dir.glob("*.json")):
        if locale_file.name in ["en.json", "qqq.json"]:
            continue

        # Load locale file once and reuse
        locale_data = load_json(locale_file)
        locale_keys = get_leaf_keys(locale_data)
        extra_keys = locale_keys - en_keys

        if extra_keys:
            errors.append(
                f"❌ {locale_file.name} has keys not in en.json: {sorted(extra_keys)}"
            )
        else:
            print(f"   ✅ {locale_file.name} keys are valid subset")

        # Check translation quality using already-loaded data
        issues = validate_translation_quality_from_data(locale_data, en_values)
        if issues:
            quality_issues[locale_file.name] = issues

    # Report quality issues as warnings
    if quality_issues:
        print()
        print("⚠️  Translation quality warnings:")
        max_issues_to_show = 5
        for locale_name, issues in quality_issues.items():
            print(f"   {locale_name}:")
            for issue in issues[:max_issues_to_show]:
                print(f"      {issue}")
            if len(issues) > max_issues_to_show:
                print(f"      ... and {len(issues) - max_issues_to_show} more issues")

    print()

    # Check language completeness (CONTRIBUTING.md requirements)
    print("🌍 Checking language completeness...")

    # Get all language codes from locale files
    all_language_codes = [
        f.stem
        for f in locales_dir.glob("*.json")
        if f.name not in ["en.json", "qqq.json"]
    ]

    # Special language codes that are metadata-only (not UI languages)
    # These need locale files and languageNames entries but not i18n.ts entries
    metadata_only_languages = {
        "mul",
    }

    # Check i18n.ts for supported languages
    i18n_ts_path = ui_src_dir / "plugins" / "i18n.ts"
    if not i18n_ts_path.exists():
        errors.append(f"❌ Missing ui/src/plugins/i18n.ts at {i18n_ts_path}")
    else:
        i18n_ts_content = i18n_ts_path.read_text(encoding="utf-8")
        # Extract language codes from supportedLanguages array
        # Looking for patterns like: { code: 'af', display: '...', rtl: ... }
        i18n_codes = set(re.findall(r"code:\s*['\"]([^'\"]+)['\"]", i18n_ts_content))

        for lang_code in all_language_codes:
            language_name_key = f"languageNames.{lang_code}"

            # Check all required locations
            missing = []
            if language_name_key not in en_keys:
                missing.append(f"   ❌ Missing languageNames.{lang_code} in en.json")
            if language_name_key not in qqq_keys:
                missing.append(f"   ❌ Missing languageNames.{lang_code} in qqq.json")

            # Metadata-only languages don't need to be in i18n.ts
            if lang_code not in metadata_only_languages and lang_code not in i18n_codes:
                missing.append(
                    f"   ❌ Missing '{lang_code}' in ui/src/plugins/i18n.ts "
                    "supportedLanguages"
                )

            if missing:
                errors.append(f"❌ Language '{lang_code}' is incomplete:")
                errors.extend(missing)
            elif lang_code in metadata_only_languages:
                print(f"   ✅ {lang_code} is complete (metadata-only)")
            else:
                print(f"   ✅ {lang_code} is complete")

    print()

    # Extract keys from code
    print("🔎 Extracting keys from code...")
    code_keys: set[str] = set()
    key_locations: dict[str, list[str]] = {}

    process_files(
        ui_src_dir, {"*.vue": "vue", "*.ts": "vue"}, repo_root, code_keys, key_locations
    )
    process_files(
        scraper_src_dir,
        {"*.py": "python", "*.html": "html"},
        repo_root,
        code_keys,
        key_locations,
    )

    print(f"   Total unique keys used in code: {len(code_keys)}")
    print()

    # Cross-validate code vs locale files
    print("🔗 Cross-validating code vs. locale files...")

    # Keys used in code but not in en.json
    missing_in_locales = code_keys - en_keys
    if missing_in_locales:
        errors.append(
            f"❌ Keys used in code but missing in en.json ({len(missing_in_locales)}):"
        )
        for key in sorted(missing_in_locales):
            files = ", ".join(key_locations[key])
            errors.append(f"   - {key} (used in: {files})")
    else:
        print("   ✅ All code keys exist in en.json")

    # Keys in en.json but not used in code
    ignored_keys = get_ignored_keys(locales_dir, en_data)
    unused_keys = {
        key for key in en_keys if key not in ignored_keys and key not in code_keys
    }

    if unused_keys:
        errors.append(f"❌ Keys in en.json but not used in code ({len(unused_keys)}):")
        for key in sorted(unused_keys):
            errors.append(f"   - {key}")
    else:
        print("   ✅ All en.json keys are used in code")

    print()

    # Report results
    if errors:
        print("❌ Validation failed!\n")
        for error in errors:
            print(error)
        return 1

    print("✅ All i18n validation checks passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
