#!/usr/bin/env python3
"""Restore Claude Desktop (macOS) from backup and remove locale setting.

Restores backed-up files and removes locale=zh-CN + claudeZhCnFont from user config.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


BACKUP_BASE = Path.home() / "Library" / "Application Support" / "Claude-zh-CN-backup"
BACKUP_JSON_ONLY = BACKUP_BASE / "json-only"
BACKUP_CHUNKS = BACKUP_BASE / "chunks"
CONFIG_PATH = Path.home() / "Library" / "Application Support" / "Claude" / "config.json"
FONT_KEY = "claudeZhCnFont"

DEFAULT_APP_RESOURCES = Path("/Applications/Claude.app/Contents/Resources")


def find_claude_resources() -> Path | None:
    if DEFAULT_APP_RESOURCES.exists() and (DEFAULT_APP_RESOURCES / "en-US.json").exists():
        return DEFAULT_APP_RESOURCES
    candidates = sorted(Path("/Applications").glob("Claude*.app/Contents/Resources/en-US.json"))
    if candidates:
        return candidates[0].parent
    candidates = sorted(Path.home().glob("Applications/Claude*.app/Contents/Resources/en-US.json"))
    if candidates:
        return candidates[0].parent
    return None


def restore_from(backup_root: Path, target: Path) -> int:
    restored = 0
    for src in backup_root.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(backup_root)
        dst = target / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(src, dst)
            restored += 1
        except PermissionError:
            print(f"Warning: permission denied copying to {dst}; try with sudo")
    return restored


def remove_locale() -> bool:
    if not CONFIG_PATH.exists():
        return False

    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False

    changed = False
    if "locale" in data:
        del data["locale"]
        changed = True
    if FONT_KEY in data:
        del data[FONT_KEY]
        changed = True

    if not changed:
        return False

    CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore Claude Desktop (macOS) from backup")
    parser.add_argument("--app-dir", type=str, default=None,
                        help="Path to Claude Resources directory")
    args = parser.parse_args()

    if args.app_dir:
        app_resources = Path(args.app_dir)
    else:
        app_resources = find_claude_resources()

    if not app_resources or not app_resources.exists():
        raise SystemExit("Claude Resources directory not found. Use --app-dir to specify manually.")

    candidates = []
    if BACKUP_JSON_ONLY.exists() and any(BACKUP_JSON_ONLY.rglob("*")):
        candidates.append(("json-only", BACKUP_JSON_ONLY, app_resources))
    if BACKUP_CHUNKS.exists() and any(BACKUP_CHUNKS.rglob("*")):
        assets_dir = app_resources / "ion-dist" / "assets" / "v1"
        candidates.append(("chunks", BACKUP_CHUNKS, assets_dir))

    if not candidates:
        print("No backup found. Will attempt manual cleanup.")
        targets = [
            app_resources / "zh-CN.json",
            app_resources / "ion-dist" / "i18n" / "zh-CN.json",
            app_resources / "ion-dist" / "i18n" / "statsig" / "zh-CN.json",
        ]
        for t in targets:
            if t.exists():
                t.unlink()
                print(f"  Removed: {t}")

        # Remove zh-CN from whitelist
        assets_dir = app_resources / "ion-dist" / "assets" / "v1"
        for f in sorted(assets_dir.glob("index-*.js")):
            content = f.read_text(encoding="utf-8")
            if '"zh-CN"' in content:
                content = content.replace(',"zh-CN"', "")
                f.write_text(content, encoding="utf-8")
                print(f"  Removed zh-CN from whitelist: {f.name}")
    else:
        total_restored = 0
        for label, root, target in candidates:
            count = restore_from(root, target)
            total_restored += count
            print(f"  Restored from {label}: {count} files")
        print(f"Total restored files: {total_restored}")

    locale_removed = remove_locale()

    print()
    print("Done")
    print(f"Locale removed: {locale_removed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
