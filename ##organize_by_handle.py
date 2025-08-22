#!/usr/bin/env python3
"""
Organize a flat folder of images into subfolders by inferred Instagram-like handles
from filenames. Prefers handles at the START of the name. No recursion.

This version PRESERVES the exact handle as it appears at the start of the filename:
- Keeps leading underscores/dots (e.g., "__zzz___oo0" stays "__zzz___oo0").
- Preserves original casing (no lowercasing).
- Still trims off numeric/date tails following the handle.

Fixes (2025-08-23):
- Trailing-handle regex now works on the stem (no extension), covering date/ID tails.
- "@ anywhere" fallback now validated with has-letter + not-camera-prefix checks.
- Removed copy option (move-only; keep --dry-run).
- CSV logging is CSV-safe (uses csv module) and does not mix summary rows.
- Log path parent directories are created automatically.
- Camera prefix filter is less aggressive (requires exact token or delimiter after prefix).
- Numeric/date tails trimmed even when there is no underscore before digits.

Intentionally NOT changed: leading-dot folders may be hidden on Unix; case differences create separate folders.
"""

import argparse
import re
import shutil
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

# ===== Heuristics =====
RE_AT_ANY = re.compile(r'@([A-Za-z0-9._]{3,30})')
# Works on *stem* (no extension). Accepts optional separators then a big number or YYYYMMDD/variants to the end.
RE_TRAILING = re.compile(r'([A-Za-z0-9._]{3,30})(?=[\s\-\._\(\)\[\]\#]*(?:\d{6,}|\d{4}[-._]?\d{2}[-._]?\d{2})?$)')

CAMERA_PREFIXES = (
    'img', 'dsc', 'pxl', 'vid', 'photo', 'screenshot', 'whatsapp', 'signal',
    'snapchat', 'instagram', 'insta', 'fb', 'telegram'
)

def has_letter(s: str) -> bool:
    return any('a' <= c.lower() <= 'z' for c in s)

def looks_like_camera_prefix(token: str) -> bool:
    t = token.strip('._').lower()
    for p in CAMERA_PREFIXES:
        if t == p or t.startswith(p + '_') or t.startswith(p + '-') or t.startswith(p + '.') or t.startswith(p + ' '):
            return True
    return False

def take_leading_handle_token_preserve(stem: str) -> Optional[str]:
    """
    Extract the first token (handle) at the VERY START of the name, preserving:
      - leading underscores/dots,
      - original casing.

    Steps:
      1) Skip decorative junk until we hit an allowed start char: [A-Za-z0-9@_.]
      2) If first allowed char is '@', drop just the '@'.
      3) Collect allowed chars [A-Za-z0-9._] up to first hard separator.
      4) Cut numeric/date tail (with or without underscore before digits).
      5) Validate: length 3..30, contains a letter, not a camera prefix.
    """
    # 1) Skip non-allowed decorations only (DO NOT strip leading '_' or '.')
    i = 0
    n = len(stem)
    while i < n and not (stem[i].isalnum() or stem[i] in {'@', '_', '.'}):
        i += 1
    stem = stem[i:]
    if not stem:
        return None

    # 2) Drop leading '@' if present, but keep subsequent underscores/dots as-is
    if stem and stem[0] == '@':
        stem = stem[1:]

    # 3) Collect token
    token_chars = []
    for ch in stem:
        if ch.isalnum() or ch in '._':
            token_chars.append(ch)
            if len(token_chars) >= 30:
                break
        else:
            break
    token = ''.join(token_chars)

    # 4) Cut numeric/date tail after the token, with or without underscore
    m = re.match(r'^(.*?)(?:[_\-\.]?(?:\d{6,}|\d{4}[-._]?\d{2}[-._]?\d{2}))$', token)
    if m:
        token = m.group(1) or token

    # 5) Validate (do NOT strip trailing '_' or '.')
    if len(token) < 3:
        return None
    if not has_letter(token):
        return None
    if looks_like_camera_prefix(token):
        return None
    return token  # preserve original casing and leading underscores/dots


def infer_handle(stem: str, *, strict_start: bool, allow_trailing: bool) -> Optional[str]:
    # Try start-of-name (preserving exact handle form)
    token = take_leading_handle_token_preserve(stem)
    if token:
        return token

    if strict_start:
        return None

    # Fallbacks (these are rarely hit if you use --strict-start)
    m = RE_AT_ANY.search(stem)
    if m:
        candidate = m.group(1)
        if has_letter(candidate) and not looks_like_camera_prefix(candidate):
            return candidate

    if allow_trailing:
        m = RE_TRAILING.search(stem)
        if m:
            candidate = m.group(1)
            if has_letter(candidate) and not looks_like_camera_prefix(candidate):
                return candidate

    return None


def iter_image_files(root: Path, allowed_exts: Iterable[str]) -> Iterable[Path]:
    exts = {e.lower().lstrip('.') for e in allowed_exts}
    for entry in sorted(root.iterdir()):
        if entry.is_file():
            ext = entry.suffix.lower().lstrip('.')
            if ext in exts:
                yield entry


def safe_move_or_copy(src: Path, dst: Path) -> Path:
    target = dst
    if target.exists():
        stem, ext = target.stem, target.suffix
        i = 1
        while target.exists():
            target = target.with_name(f"{stem}__{i}{ext}")
            i += 1
    try:
        src.rename(target)
    except OSError:
        shutil.move(str(src), str(target))
    return target


def organize(root: Path, min_count: int, include_singletons: bool,
             allowed_exts: List[str], dry_run: bool, log_path: Optional[Path],
             strict_start: bool, allow_trailing: bool) -> None:

    groups: Dict[str, List[Path]] = defaultdict(list)
    ungrouped: List[Path] = []

    files = list(iter_image_files(root, allowed_exts))
    for f in files:
        handle = infer_handle(f.stem, strict_start=strict_start, allow_trailing=allow_trailing)
        if handle:
            groups[handle].append(f)
        else:
            ungrouped.append(f)

    # Choose which groups to operate on
    selected: Dict[str, List[Path]] = {}
    for handle, paths in groups.items():
        if len(paths) >= min_count or include_singletons:
            selected[handle] = paths

    # Plan moves
    planned: List[Tuple[Path, Path, str]] = []
    for handle, paths in selected.items():
        dest_dir = root / handle  # preserve exact handle (leading dot/underscore, case, etc.)
        for src in paths:
            planned.append((src, dest_dir / src.name, handle))

    # Logging rows
    log_rows: List[Tuple[str, str, str, str]] = []

    # Execute
    for src, dst, handle in planned:
        if dry_run:
            action = "MOVE"
            print(f"[DRY-RUN] {action} {src.name}  ->  {handle}/")
            if log_path:
                log_rows.append((f"DRY-{action}", handle, str(src), str(dst)))
            continue

        dst.parent.mkdir(parents=True, exist_ok=True)
        final_dst = safe_move_or_copy(src, dst)
        action = "MOVED"
        print(f"{action}: {src.name} -> {final_dst}")
        if log_path:
            log_rows.append((action, handle, str(src), str(final_dst)))

    # Write CSV log (actions only)
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["action","handle","src","dst"])
            for row in log_rows:
                w.writerow(list(row))

    print("\n--- SUMMARY ---")
    print(f"Scanned files: {len(files)}  (flat, no recursion)")
    print(f"Groups found: {len(groups)}")
    print(f"Groups selected: {len(selected)} (min_count={min_count}, include_singletons={include_singletons})")
    print(f"Planned ops: {len(planned)}")
    if ungrouped:
        print(f"Ungrouped: {len(ungrouped)} (files without a valid handle)")


def main():
    parser = argparse.ArgumentParser(description="Organize images into folders by inferred handles (prefers start-of-name; preserves exact handle form).")
    parser.add_argument("folder", type=str, help="Path to the folder containing images (flat, no recursion).")
    parser.add_argument("--min-count", type=int, default=3, help="Minimum files required to create a folder for a handle (default: 3).")
    parser.add_argument("--include-singletons", action="store_true", help="Also organize single-file handles (can create many tiny folders).")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without moving files.")
    parser.add_argument("--ext", nargs="+", default=["jpg", "jpeg", "png", "webp", "heic"], help="Allowed file extensions to scan.")
    parser.add_argument("--log", type=str, default=None, help="Optional CSV log path to write actions (CSV).")
    parser.add_argument("--strict-start", action="store_true", help="Only accept handles at the very start of filename (after skipping decoration).")
    parser.add_argument("--no-trailing", action="store_true", help="Disable trailing-handle heuristic.")
    args = parser.parse_args()

    root = Path(args.folder).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Folder not found or not a directory: {root}")

    log_path = Path(args.log).expanduser().resolve() if args.log else None

    organize(
        root=root,
        min_count=args.min_count,
        include_singletons=args.include_singletons,
        allowed_exts=args.ext,
        dry_run=args.dry_run,
        log_path=log_path,
        strict_start=args.strict_start,
        allow_trailing=not args.no_trailing,
    )

if __name__ == "__main__":
    main()
