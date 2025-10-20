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
    with open(path, encoding="utf-8") as f:
        return json.load(f)  # type: ignore


def get_all_keys(data: dict[str, Any], prefix: str = "") -> tuple[set[str], set[str]]:
    """Recursively extract all keys from nested dictionary.

    Args:
        data: The dictionary to extract keys from
        prefix: The current key prefix
        parent_keys: If True, include parent keys (keys with dict values) in addition to
                    leaf keys. This is useful for i18n systems where code references
                    parent keys (e.g., 'ui_strings.about-1') and the system applies
                    the appropriate property (e.g., '.textContent').

    Returns:
        A tuple of (all_keys, parent_keys_set) where all_keys includes both parent
        and leaf keys if parent_keys=True, and parent_keys_set contains only the
        parent keys (keys that have children).
    """
    all_keys: set[str] = set()
    parent_keys_set: set[str] = set()

    for key, value in data.items():
        # Skip metadata
        if key == "@metadata":
            continue
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            # This is a parent key
            parent_keys_set.add(full_key)
            all_keys.add(full_key)
            child_keys, child_parents = get_all_keys(
                value,  # pyright: ignore[reportUnknownArgumentType]
                full_key,
            )
            all_keys.update(child_keys)
            parent_keys_set.update(child_parents)
        else:
            # Always add leaf keys
            all_keys.add(full_key)
    return all_keys, parent_keys_set


def extract_keys_from_python(file_path: Path) -> set[str]:
    """Extract i18n keys from Python files."""
    content = file_path.read_text(encoding="utf-8")
    # Match: i18n.t("key" or i18n.t('key'
    pattern = r'i18n\.t\s*\(\s*["\']([^"\']+)["\']'
    return set(re.findall(pattern, content))


def extract_keys_from_html_templates(file_path: Path) -> set[str]:
    """Extract i18n keys from HTML templates using data-l10n-id attributes."""
    content = file_path.read_text(encoding="utf-8")
    keys: set[str] = set()
    # Match: data-l10n-id="key" or data-l10n-id='key'
    pattern = r'data-l10n-id\s*=\s*["\']([^"\']+)["\']'
    found_keys = re.findall(pattern, content)
    # Prefix keys with ui_strings since that's the structure in locale files
    for key in found_keys:
        # Skip dynamic keys with Jinja template variables ({{ ... }})
        if "{{" not in key:
            keys.add(f"ui_strings.{key}")
    return keys


def extract_keys_from_javascript(file_path: Path) -> set[str]:
    """Extract i18n keys from JavaScript files using data-l10n-id."""
    content = file_path.read_text(encoding="utf-8")
    keys: set[str] = set()
    # Match: data-l10n-id="key" or data-l10n-id='key' in strings
    pattern1 = r'data-l10n-id\s*=\s*["\']([^"\']+)["\']'
    found_keys = re.findall(pattern1, content)
    # Match: .attr("data-l10n-id", "key") or .attr('data-l10n-id', 'key')
    pattern2 = r'\.attr\s*\(\s*["\']data-l10n-id["\']\s*,\s*["\']([^"\']+)["\']'
    found_keys.extend(re.findall(pattern2, content))
    # Prefix keys with ui_strings since that's the structure in locale files
    for key in found_keys:
        if "{{" not in key:
            keys.add(f"ui_strings.{key}")
    return keys


def main() -> int:
    """Main validation function."""
    # Find repository root (go up from this script location)
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent.parent
    locales_dir = repo_root / "locales"
    src_dir = repo_root / "src"

    print("🔍 Validating i18n translations...")
    print()

    errors: list[str] = []

    # 0. Check required directories and files exist
    print("📂 Checking required directories and files...")
    required_paths = [
        (locales_dir, "locales directory"),
        (src_dir, "src directory"),
    ]

    for path, description in required_paths:
        if not path.exists():
            print(f"   ❌ Missing {description}: {path}")
            return 1
        print(f"   ✅ Found {description}")

    print()

    # 1. Load and validate locale files
    print("📁 Checking locale files...")
    en_path = locales_dir / "en.json"
    qqq_path = locales_dir / "qqq.json"

    if not en_path.exists():
        errors.append(f"❌ Missing en.json at {en_path}")
        return 1

    if not qqq_path.exists():
        errors.append(f"❌ Missing qqq.json at {qqq_path}")
        return 1

    en_data = load_json(en_path)
    qqq_data = load_json(qqq_path)

    en_keys, en_parent_keys = get_all_keys(en_data)
    qqq_keys, _ = get_all_keys(qqq_data)

    print(f"   Found {len(en_keys)} keys in en.json")
    print(f"   Found {len(qqq_keys)} keys in qqq.json")

    # Check en.json and qqq.json have matching keys
    if en_keys != qqq_keys:
        errors.append("❌ Keys in en.json and qqq.json do not match!")
        missing_in_qqq = en_keys - qqq_keys
        missing_in_en = qqq_keys - en_keys
        if missing_in_qqq:
            errors.append(f"   Missing in qqq.json: {sorted(missing_in_qqq)}")
        if missing_in_en:
            errors.append(f"   Extra in qqq.json: {sorted(missing_in_en)}")
    else:
        print("   ✅ en.json and qqq.json keys match")

    # Check other locale files
    for locale_file in sorted(locales_dir.glob("*.json")):
        if locale_file.name in ["en.json", "qqq.json"]:
            continue
        locale_data = load_json(locale_file)
        locale_keys, _ = get_all_keys(locale_data)
        extra_keys = locale_keys - en_keys
        if extra_keys:
            errors.append(
                f"❌ {locale_file.name} has keys not in en.json: {sorted(extra_keys)}"
            )
        else:
            print(f"   ✅ {locale_file.name} keys are valid subset")

    print()

    # 2. Extract keys from code
    print("🔎 Extracting keys from code...")
    code_keys: set[str] = set()
    # Track which files use which keys
    key_locations: dict[str, list[str]] = {}

    # Python files
    for py_file in src_dir.rglob("*.py"):
        # Skip node_modules and this validation script itself
        if "node_modules" in str(py_file) or py_file.samefile(Path(__file__)):
            continue
        keys = extract_keys_from_python(py_file)
        if keys:
            print(f"   Found {len(keys)} keys in {py_file.relative_to(repo_root)}")
            code_keys.update(keys)
            for key in keys:
                key_locations.setdefault(key, []).append(
                    str(py_file.relative_to(repo_root))
                )

    # HTML templates
    for html_file in src_dir.rglob("*.html"):
        if "node_modules" in str(html_file):
            continue
        keys = extract_keys_from_html_templates(html_file)
        if keys:
            rel_path = html_file.relative_to(repo_root)
            print(f"   Found {len(keys)} keys in {rel_path}")
            code_keys.update(keys)
            for key in keys:
                key_locations.setdefault(key, []).append(
                    str(html_file.relative_to(repo_root))
                )

    # JavaScript files
    for js_file in src_dir.rglob("*.js"):
        if "node_modules" in str(js_file):
            continue
        keys = extract_keys_from_javascript(js_file)
        if keys:
            print(f"   Found {len(keys)} keys in {js_file.relative_to(repo_root)}")
            code_keys.update(keys)
            for key in keys:
                key_locations.setdefault(key, []).append(
                    str(js_file.relative_to(repo_root))
                )

    print(f"   Total unique keys used in code: {len(code_keys)}")
    print()

    # 3. Cross-validate
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
    # When checking for unused keys, we need to account for the fact that:
    # - Parent keys (e.g., 'ui_strings.about-1') are referenced in code
    # - Their leaf children (e.g., 'ui_strings.about-1.textContent') are used by the
    #   l10n system but not directly referenced in code
    # So we should only report keys as unused if:
    # 1. They are not referenced in code, AND
    # 2. Their parent (if they have one) is also not referenced in code
    ignored_keys = {"ui_strings.isocode", "ui_strings.autonym"}

    unused_keys = set()
    for key in en_keys:
        if key in ignored_keys or key in code_keys:
            continue
        # Check if this key's parent is used in code
        # If parent is used, the l10n system will use this child key
        parent_used = False
        for parent in en_parent_keys:
            if key.startswith(f"{parent}.") and parent in code_keys:
                parent_used = True
                break
        if not parent_used:
            unused_keys.add(key)

    if unused_keys:
        errors.append(f"❌ Keys in en.json but not used in code ({len(unused_keys)}):")
        for key in sorted(unused_keys):
            errors.append(f"   - {key}")
    else:
        print("   ✅ All en.json keys are used in code")

    print()

    # 4. Report results
    if errors:
        print("❌ Validation failed!\n")
        for error in errors:
            print(error)
        return 1
    else:
        print("✅ All i18n validation checks passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
