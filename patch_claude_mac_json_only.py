#!/usr/bin/env python3
"""Patch JSON i18n resources in Claude Desktop for macOS.

Accepts --app-dir to specify the Claude Resources directory.
Defaults to /Applications/Claude.app/Contents/Resources.

Steps:
1. Backup original files
2. Copy zh-CN JSON resources into the app bundle
3. Patch the language whitelist in index-*.js to recognize zh-CN
4. Set locale=zh-CN in user config
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RESOURCES = ROOT / "resources"
DEFAULT_APP_RESOURCES = Path("/Applications/Claude.app/Contents/Resources")
BACKUP_ROOT = Path.home() / "Library" / "Application Support" / "Claude-zh-CN-backup" / "json-only"
CONFIG_PATH = Path.home() / "Library" / "Application Support" / "Claude" / "config.json"


def find_claude_resources() -> Path | None:
    if DEFAULT_APP_RESOURCES.exists() and (DEFAULT_APP_RESOURCES / "en-US.json").exists():
        return DEFAULT_APP_RESOURCES
    candidates = sorted(Path("/Applications").glob("Claude*.app/Contents/Resources/en-US.json"))
    if candidates:
        return candidates[0].parent
    candidates = sorted(Path.home().glob("Applications/Claude*.app/Contents/Resources/en-US.json"))
    if candidates:
        return candidates[0].parent
    candidates = sorted(Path("/Applications").glob("Claude*/Contents/Resources/en-US.json"))
    if candidates:
        return candidates[0].parent
    return None


def backup_file(path: Path, app_resources: Path) -> None:
    if not path.exists():
        return
    rel = path.relative_to(app_resources)
    dst = BACKUP_ROOT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        shutil.copy2(path, dst)


def patch_whitelist(app_resources: Path) -> str | None:
    assets_dir = app_resources / "ion-dist" / "assets" / "v1"
    candidates = sorted(assets_dir.glob("index-*.js"))
    if not candidates:
        print("Warning: no index-*.js found; skipping whitelist patch")
        return None

    for path in candidates:
        text = path.read_text(encoding="utf-8")
        backup_file(path, app_resources)

        if '"zh-CN"' in text:
            return path.name

        pattern = re.compile(r'(\["en-US"(?:,"[a-zA-Z]{2,3}(?:-[a-zA-Z0-9]{2,4})*")+)\]')
        m = pattern.search(text)
        if m:
            original_array = m.group(0)
            patched_array = original_array[:-1] + ',"zh-CN"]'
            text = text.replace(original_array, patched_array, 1)
            path.write_text(text, encoding="utf-8")
            return path.name

    print("Warning: whitelist pattern not found in any index bundle")
    return None


def set_locale() -> bool:
    if not CONFIG_PATH.exists():
        print(f"Warning: config not found at {CONFIG_PATH}; skipping locale")
        return False

    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: cannot parse config: {e}; skipping locale")
        return False

    if data.get("locale") == "zh-CN":
        return True

    data["locale"] = "zh-CN"
    CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Patch Claude Desktop (macOS) with zh-CN resources")
    parser.add_argument("--app-dir", type=str, default=None,
                        help="Path to Claude Resources directory (auto-detected if omitted)")
    args = parser.parse_args()

    if args.app_dir:
        app_resources = Path(args.app_dir)
    else:
        app_resources = find_claude_resources()

    if not app_resources or not app_resources.exists():
        raise SystemExit(
            "Claude Resources directory not found.\n"
            "Use --app-dir to specify manually, e.g.:\n"
            "  python patch_claude_mac_json_only.py --app-dir /Applications/Claude.app/Contents/Resources"
        )

    if not (app_resources / "en-US.json").exists():
        raise SystemExit(f"en-US.json not found in: {app_resources}\n"
                         "Is this the correct Claude Resources directory?")

    files = [
        (RESOURCES / "desktop-zh-CN.json", app_resources / "zh-CN.json"),
        (RESOURCES / "frontend-zh-CN.json", app_resources / "ion-dist" / "i18n" / "zh-CN.json"),
        (RESOURCES / "statsig-zh-CN.json", app_resources / "ion-dist" / "i18n" / "statsig" / "zh-CN.json"),
    ]

    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

    copied = 0
    for src, dst in files:
        if not src.exists():
            raise SystemExit(f"Missing source resource: {src}")
        backup_file(dst, app_resources)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1

    wl_file = patch_whitelist(app_resources)
    locale_set = set_locale()

    print("Done")
    print(f"Resources dir: {app_resources}")
    print(f"Copied json resources: {copied}")
    print(f"Whitelist patched: {wl_file or 'skipped'}")
    print(f"Locale set: {locale_set}")
    print(f"Backup root: {BACKUP_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
