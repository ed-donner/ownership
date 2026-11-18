"""Generate docs/specs/modules.md from the manifests in addons/ (stdlib only)."""
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADDONS = ROOT / "addons"
OUT = ROOT / "docs" / "specs" / "modules.md"
MAX_DEPENDS = 8
MAX_SUMMARY = 160


def load_manifest(path):
    try:
        data = ast.literal_eval(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (ValueError, SyntaxError, OSError):
        return {}


def clean(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def first_sentence(text):
    text = clean(text)
    m = re.match(r"(.+?[.!?])(\s|$)", text)
    return m.group(1) if m else text


def describe(name, man):
    text = clean(man.get("summary"))
    if not text:
        text = first_sentence(man.get("description"))
    if not text:
        text = clean(man.get("name")) or name
    if len(text) > MAX_SUMMARY:
        text = text[: MAX_SUMMARY - 3].rstrip() + "..."
    return text


def depends(man):
    deps = man.get("depends")
    if not isinstance(deps, (list, tuple)):
        return "?" if man == {} else "none"
    deps = [str(d) for d in deps]
    if not deps:
        return "none"
    if len(deps) > MAX_DEPENDS:
        return ", ".join(deps[:MAX_DEPENDS]) + f", +{len(deps) - MAX_DEPENDS} more"
    return ", ".join(deps)


def main():
    mods = sorted(p.parent for p in ADDONS.glob("*/__manifest__.py"))
    lines = [
        "# Module index",
        "",
        f"{len(mods)} modules in `addons/`. Generated file, do not edit by hand.",
        "Regenerate with `uv run docs/gen_modules.py` (reads `addons/*/__manifest__.py`).",
        "",
    ]
    for d in sorted(mods, key=lambda p: p.name):
        man = load_manifest(d / "__manifest__.py")
        lines.append(f"- `addons/{d.name}` - {describe(d.name, man)} (depends: {depends(man)})")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(mods)} modules")


if __name__ == "__main__":
    main()
