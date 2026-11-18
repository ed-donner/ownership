"""Check that every repo path cited in the agent docs exists.

Usage: uv run docs/check_citations.py
"""

import glob
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTS = ("py", "xml", "js", "scss", "csv", "md", "conf", "txt", "cfg")
SKIP_PREFIXES = ("addons/take_ownership/",)

TICK_RE = re.compile(r"`([^`\n]+)`")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
LINE_SUFFIX_RE = re.compile(r"(:\d+(-\d+)?)+$")
EXT_RE = re.compile(r"\.(%s)$" % "|".join(EXTS))
PATH_CHARS_RE = re.compile(r"^[\w./*@+\-\[\]{}~]+$")
URL_RE = re.compile(r"^[a-z][a-z0-9+.-]*://|^mailto:", re.I)


def doc_files():
    files = [ROOT / "AGENTS.md", ROOT / "docs" / "spec.md"]
    files += sorted((ROOT / "docs" / "specs").glob("*.md"))
    return files


def looks_like_path(tok):
    if " " in tok or URL_RE.match(tok):
        return False
    if not PATH_CHARS_RE.match(tok):
        return False
    return "/" in tok or bool(EXT_RE.search(tok))


def exists(rel, base):
    """Return True if rel exists (glob-aware) relative to base."""
    if any(c in rel for c in "*?"):
        return bool(glob.glob(str(base / rel), recursive=True))
    return (base / rel).exists()


def clean(tok):
    tok = LINE_SUFFIX_RE.sub("", tok)
    return tok.split("#", 1)[0]


def main():
    checked = missing = skipped = 0
    expected = [ROOT / "AGENTS.md", ROOT / "docs" / "spec.md"]
    for f in expected:
        if not f.exists():
            print(f"DOC MISSING: {f.relative_to(ROOT)} (writer may have failed)")
            missing += 1
    specs = list((ROOT / "docs" / "specs").glob("*.md"))
    if not specs:
        print("DOC MISSING: docs/specs/*.md (no area files found)")
        missing += 1
    for doc in doc_files():
        if not doc.exists():
            continue
        rel_doc = doc.relative_to(ROOT)
        in_fence = False
        for lineno, line in enumerate(doc.read_text().splitlines(), 1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            cands = []
            for m in TICK_RE.finditer(line):
                tok = clean(m.group(1))
                if looks_like_path(tok):
                    cands.append((tok, ROOT))
            for m in LINK_RE.finditer(line):
                tok = clean(m.group(1))
                if not tok or URL_RE.match(tok) or tok.startswith("#"):
                    continue
                cands.append((tok, doc.parent))
            for tok, base in cands:
                norm = tok.lstrip("/") if base == ROOT else tok
                try:
                    shown = (base / norm).resolve().relative_to(ROOT).as_posix()
                except ValueError:
                    shown = norm
                if any(shown.startswith(p) for p in SKIP_PREFIXES):
                    skipped += 1
                    continue
                checked += 1
                if not exists(norm, base):
                    missing += 1
                    print(f"{rel_doc}:{lineno}: missing {tok}")
    print(f"checked={checked} missing={missing} skipped_to_be_created={skipped}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
