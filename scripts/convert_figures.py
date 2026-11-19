#!/usr/bin/env python3
"""Convert <!-- FIGURE: file | caption --> markers into real markdown image embeds.

Run once the figure files exist:  python3 scripts/convert_figures.py
- Chapters/appendices already containing a real image embed for the same file are left alone.
- If the SVG is missing, the marker is left in place (Phase 5 gap).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIG_RE = re.compile(r"<!--\s*FIGURE:\s*(\S+)\s*\|\s*([^>]+?)\s*-->")

converted = 0
skipped = 0
for sub in ("chapters", "appendices", "front-matter"):
    d = ROOT / sub
    if not d.exists():
        continue
    for p in sorted(d.glob("*.md")):
        text = p.read_text()
        changed = False

        def repl(m):
            global converted, skipped, changed
            fname, caption = m.group(1), m.group(2).strip()
            img = ROOT / "images" / fname
            if not img.exists():
                skipped += 1
                return m.group(0)
            if f"](" in caption or f"![{caption}]" in text:
                return m.group(0)
            changed = True
            converted += 1
            return f"![{caption}](../images/{fname})"

        new = FIG_RE.sub(repl, text)
        if changed:
            p.write_text(new)
            print("updated", p.relative_to(ROOT))
print(f"converted {converted} markers, {skipped} left pending (missing art)")
