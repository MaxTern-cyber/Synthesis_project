"""
Normalize user-facing documentation to plain ASCII.

1. Strip UTF-8 BOM.
2. Recover mojibake (UTF-8 bytes that were once decoded as Latin-1/CP1252
   and re-saved as UTF-8) when possible.
3. Replace common typographic / arrow / math / emoji glyphs with ASCII
   equivalents so rendering is identical in every terminal / editor / VCS.

Run from repo root:
    python launchers/fix_unicode.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TARGETS = [
    "README.md",
    "CONTRIBUTING.md",
    "samples/README.md",
    "outputs/README.md",
    "docs/QUICK_START.md",
    "docs/ENHANCEMENTS_SUMMARY.md",
    "docs/LINKEDIN_POST.md",
    "docs/BLOG_POST.md",
    "docs/PROFILE_README_SETUP.md",
    "docs/PROFILE_README_TEMPLATE.md",
    "docs/DOCUMENTATION.md",
    "samples/generate_array_mult.py",
    "launchers/generate_sample_outputs.py",
]

# ASCII replacements for common Unicode glyphs we use.
REPLACEMENTS = {
    "\u2014": "--",     # em dash
    "\u2013": "-",      # en dash
    "\u2212": "-",      # minus sign
    "\u2018": "'",      # left single quote
    "\u2019": "'",      # right single quote
    "\u201C": '"',      # left double quote
    "\u201D": '"',      # right double quote
    "\u2026": "...",    # ellipsis
    "\u00B7": "*",      # middle dot
    "\u2022": "*",      # bullet
    "\u00D7": "x",      # multiplication
    "\u00F7": "/",      # division
    "\u2192": "->",     # right arrow
    "\u2190": "<-",     # left arrow
    "\u2194": "<->",    # left-right arrow
    "\u21D2": "=>",     # double right arrow
    "\u2265": ">=",
    "\u2264": "<=",
    "\u2260": "!=",
    "\u2248": "~=",
    "\u00B2": "^2",
    "\u00B3": "^3",
    "\u00B0": " deg",
    "\u00B1": "+/-",
    "\u00A9": "(c)",
    "\u00AE": "(R)",
    "\u2122": "(TM)",
    "\u00A0": " ",      # nbsp
    "\u200B": "",       # zero-width space
    "\u200C": "",
    "\u200D": "",
    "\uFEFF": "",       # BOM mid-stream
    # box drawing - keep simple
    "\u2500": "-",
    "\u2502": "|",
    "\u2514": "+",
    "\u251C": "+",
    "\u2518": "+",
    "\u250C": "+",
    "\u2510": "+",
    "\u2524": "+",
    "\u252C": "+",
    "\u2534": "+",
    "\u253C": "+",
    "\u2576": "-",
    "\u2577": "|",
    "\u2580": "#",
    "\u2588": "#",
    "\u25B6": ">",
    "\u25C0": "<",
    "\u25A0": "[#]",
    "\u25A1": "[ ]",
    "\u2713": "[x]",    # check
    "\u2714": "[x]",
    "\u2717": "[ ]",
    "\u2718": "[ ]",
}


def try_unmojibake(text: str) -> str:
    """If text contains UTF-8-as-Latin1 mojibake, try to recover it.

    Strategy: encode as latin-1 (recovering original bytes) then decode as UTF-8.
    Only apply when the round trip strictly improves things (i.e. removes
    the obvious mojibake markers without raising).
    """
    markers = ("\u00c3", "\u00e2\u0080", "\u00c5", "\u00f0\u0178")
    if not any(m in text for m in markers):
        return text
    try:
        recovered = text.encode("latin-1", errors="strict").decode("utf-8", errors="strict")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text
    # heuristic: prefer the version with fewer suspicious sequences.
    bad_before = sum(text.count(m) for m in markers)
    bad_after = sum(recovered.count(m) for m in markers)
    return recovered if bad_after < bad_before else text


def to_ascii(text: str) -> str:
    # 1. drop BOM at start
    if text.startswith("\ufeff"):
        text = text.lstrip("\ufeff")
    # 2. recover mojibake if present
    text = try_unmojibake(text)
    # 3. apply explicit table
    for src, dst in REPLACEMENTS.items():
        if src in text:
            text = text.replace(src, dst)
    # 4. drop everything else outside printable ASCII + tab + newline
    out_chars = []
    for ch in text:
        cp = ord(ch)
        if cp < 0x80 or ch in ("\n", "\r", "\t"):
            out_chars.append(ch)
        else:
            # last-resort: drop the char (already covered above for known ones)
            out_chars.append("")
    return "".join(out_chars)


def main() -> int:
    total_changed = 0
    for rel in TARGETS:
        path = ROOT / rel
        if not path.exists():
            print(f"  skip (missing): {rel}")
            continue
        original = path.read_text(encoding="utf-8")
        fixed = to_ascii(original)
        if fixed != original:
            path.write_text(fixed, encoding="utf-8", newline="\n")
            removed = sum(1 for c in original if ord(c) >= 0x80)
            print(f"  fixed: {rel}  ({removed} non-ASCII codepoints normalized)")
            total_changed += 1
        else:
            print(f"  clean: {rel}")
    print()
    print(f"Done. {total_changed} file(s) updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
