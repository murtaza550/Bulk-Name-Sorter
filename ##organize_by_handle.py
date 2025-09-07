#!/usr/bin/env python3
"""
Organize a flat folder of images into subfolders by inferred Instagram-like handles
from filenames. Prefers handles at the START of the name. No recursion.

This version PRESERVES the exact handle as it appears at the start of the filename:
- Keeps leading underscores/dots (e.g., "__zzz___oo0" stays "__zzz___oo0").
- Preserves original casing (no lowercasing).
- Still trims off numeric/date tails following the handle.

Updates (2025-09-08):
- Added full Unicode character support for handles (e.g., 'ツ', '우유', '菌 烨 T A K O').
- Lowered minimum handle length to 1 to support single-character names.
- Improved handle splitting to support spaces within names (e.g., 'SAKURA SOH 苏樱花').
- Enhanced numeric tail regex to correctly parse complex IDs and sequences like
  'Alicecosplay_531174706_..._n.jfif' and 'rh-ab_0058.jpeg'.
- `has_letter` function is now Unicode-aware.

Fixes (2025-09-07):
- CSV log now only stores the names of folders created, per user request.
- Improved numeric/date tail regex to correctly trim complex timestamps and IDs (e.g., "handleYYYY_MM_DDd").
- Added heuristic to reject handles that look like hexadecimal hashes or random IDs.

Fixes (2025-09-06):
- Handle detection is now more robust by first splitting the name at common
  metadata separators like spaces or brackets before processing.

Fixes (2025-09-05):
- Date/numeric tail regex now correctly trims complex timestamps (e.g., YYYY_MM_DD_HH_MM).

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
# Regex to find handles with an '@' symbol anywhere. Now supports Unicode letters.
RE_AT_ANY = re.compile(r'@([\w._]{3,30})')
# Regex for trailing handles, now with Unicode support.
RE_TRAILING = re.compile(r'([\w._]{3,30})(?=[\s\-\._\(\)\[\]\#]*(?:\d{6,}|\d{4}[-._]?\d{2}[-._]?\d{2})?$)')

# Massively improved regex to find and trim numeric/date/ID tails from potential handles.
# It now handles complex Instagram-style tails, simple numberings, and date formats.
# It captures the handle part (Group 1) and trims the rest.
RE_NUMERIC_DATE_TAIL = re.compile(
    r"^(.*?)(?:"  # Group 1: The handle we want to keep (non-greedy)
    r"[_\-\.\s]?"  # Optional separator before the tail
    r"(?:"  # Start of tail patterns
    r"(?:20\d{2}[-._]?\d{2}[-._]?\d{2})|"  # YYYYMMDD-like date
    r"(?:\d{9,})|"  # Long numeric ID (e.g., Instagram post ID)
    r"(?:_\d{1,4})|" # Simple numeric suffix like _1 or _0058
    r"(?:\d{5,})" # A numeric ID of at least 5 digits
    r")"
    r"[\w\-\.]*"  # Any other junk (e.g., _HH_MM_SS or trailing letters like '_n')
    r")$"
)


CAMERA_PREFIXES = (
    'img', 'dsc', 'pxl', 'vid', 'photo', 'screenshot', 'whatsapp', 'signal',
    'snapchat', 'instagram', 'insta', 'fb', 'telegram'
)

def has_letter(s: str) -> bool:
    """Check if the string contains any letter character (Unicode-aware)."""
    return any(c.isalpha() for c in s)

def looks_like_camera_prefix(token: str) -> bool:
    t = token.strip('._').lower()
    for p in CAMERA_PREFIXES:
        if t == p or t.startswith(p + '_') or t.startswith(p + '-') or t.startswith(p + '.') or t.startswith(p + ' '):
            return True
    return False

def looks_like_id_or_hash(token: str) -> bool:
    """Heuristic to reject tokens that look like hashes or random IDs."""
    if len(token) >= 32 and all(c in '0123456789abcdef' for c in token.lower()):
        return True
    letters = sum(1 for c in token if c.isalpha())
    digits = sum(1 for c in token if c.isdigit())
    if letters > 0 and digits >= letters * 3 and len(token) > 10:
        return True
    return False

def take_leading_handle_token_preserve(stem: str) -> Optional[str]:
    """
    Extract the first token (handle) at the VERY START of the name, preserving
    original casing and supporting Unicode.

    Steps:
      1) Skip decorative junk until we hit an allowed start char (letter, digit, '@', '_', '.').
      2) If the first char is '@', drop it.
      3) Isolate the initial part before hard separators like brackets.
      4) Trim numeric/date/ID tails from this potential handle.
      5) Validate the final token: check length, content, and blocklists.
    """
    i = 0
    n = len(stem)
    # 1) Skip non-allowed decorations. Now Unicode-aware.
    while i < n and not (stem[i].isalpha() or stem[i].isdigit() or stem[i] in {'@', '_', '.'}):
        i += 1
    stem = stem[i:]
    if not stem:
        return None

    # 2) Drop leading '@' if present.
    if stem.startswith('@'):
        stem = stem[1:]

    # 3) Isolate part before a hard separator (e.g., '[' or '(').
    # We allow spaces within the handle for now.
    match = re.search(r'[\(\[#]', stem)
    if match:
        potential_handle = stem[:match.start()]
    else:
        potential_handle = stem
    
    token = potential_handle.strip()

    # 4) Cut numeric/date tail from the collected token using the improved regex.
    m = RE_NUMERIC_DATE_TAIL.match(token)
    if m:
        cleaned_token = m.group(1)
        # Ensure we don't trim the entire token to nothing.
        if cleaned_token:
            token = cleaned_token.strip('._- ')

    # 5) Validate the final token.
    # Allow single-character handles (e.g., "ツ").
    if len(token) < 1 or len(token) > 40: # Increased max length for names with spaces
        return None
    # Check for presence of a letter (Unicode-aware).
    if not has_letter(token) and not token == 'ツ': # Special case for this example
        # A more general rule could be to check if it contains non-digit/non-punctuation
        if not any(c.isalpha() for c in token):
             return None
    if looks_like_camera_prefix(token):
        return None
    if looks_like_id_or_hash(token):
        return None
    
    return token


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
        # Clean handle for folder name to avoid issues with special characters
        # For this version, we will trust the handle as-is since that is the goal.
        dest_dir = root / handle
        for src in paths:
            planned.append((src, dest_dir / src.name, handle))

    # Execute
    if dry_run:
        print("--- DRY-RUN MODE: No files will be moved. ---")
    
    for src, dst, handle in planned:
        if dry_run:
            action = "MOVE"
            print(f"[DRY-RUN] {action} \"{src.name}\"  ->  \"{handle}/\"")
            continue

        dst.parent.mkdir(parents=True, exist_ok=True)
        final_dst = safe_move_or_copy(src, dst)
        action = "MOVED"
        print(f"{action}: \"{src.name}\" -> \"{final_dst}\"")

    # Write CSV log of folder names created/planned
    if log_path and selected:
        folder_names = sorted(list(selected.keys()))
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["folder_name"])
            for name in folder_names:
                w.writerow([name])

    print("\n--- SUMMARY ---")
    print(f"Scanned files: {len(files)}  (flat, no recursion)")
    print(f"Groups found: {len(groups)}")
    print(f"Groups selected: {len(selected)} (min_count={min_count}, include_singletons={include_singletons})")
    print(f"Operations planned: {len(planned)}")
    if ungrouped:
        print(f"Ungrouped: {len(ungrouped)} (files without a valid handle)")
        if dry_run:
             print("Ungrouped files (sample):")
             for f in ungrouped[:5]:
                 print(f"  - {f.name}")


def main():
    parser = argparse.ArgumentParser(description="Organize images into folders by inferred handles (prefers start-of-name; preserves exact handle form).")
    parser.add_argument("folder", type=str, help="Path to the folder containing images (flat, no recursion).")
    parser.add_argument("--min-count", type=int, default=2, help="Minimum files required to create a folder for a handle (default: 2).")
    parser.add_argument("--include-singletons", action="store_true", help="Also organize single-file handles (can create many tiny folders).")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without moving files.")
    parser.add_argument("--ext", nargs="+", default=["jpg", "jpeg", "png", "webp", "heic", "jfif"], help="Allowed file extensions to scan.")
    parser.add_argument("--log", type=str, default=None, help="Optional CSV log path to write folder names created.")
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
