#!/usr/bin/env python3
"""Generate _sidebar.md from the live chapter/appendix/front-matter tree."""
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

def slugify(heading):
    h = re.sub(r"[`*_]", "", heading.strip()).lower()
    h = re.sub(r"[^a-z0-9 \-]", "", h)
    h = re.sub(r"\s+", "-", h.strip())
    return re.sub(r"-+", "-", h).strip("-")

def headings(path, max_level=3):
    out, in_code = [], False
    for line in path.read_text().splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m and len(m.group(1)) <= max_level:
            out.append((len(m.group(1)), m.group(2).strip()))
    return out

PARTS = [
    ("FRONT MATTER", [
        ("front-matter/f01-title-page.md", None),
        ("front-matter/f02-authors.md", None),
        ("front-matter/f03-copyright.md", None),
        ("front-matter/f04-preface.md", None),
        ("front-matter/f05-how-to-read.md", None),
        ("front-matter/f06-table-of-contents.md", None),
        ("front-matter/f07-list-of-figures.md", None),
    ]),
    ("PART I — FOUNDATIONS", ["chapters/ch01-riverbrand-story.md", "chapters/ch02-learn-unlearn-relearn.md", "chapters/ch03-domain-primer.md"]),
    ("PART II — MONEY MOVEMENT", ["chapters/ch04-for-everyone-how-money-moves.md", "chapters/ch05-engineering-transaction-engine.md"]),
    ("PART III — WEALTH AND CHANNELS", ["chapters/ch06-for-everyone-wealth-and-channels.md", "chapters/ch07-engineering-channel-fabric.md"]),
    ("PART IV — TRUST AND COMPLIANCE", ["chapters/ch08-for-everyone-safety-and-compliance.md", "chapters/ch09-engineering-security-architecture.md"]),
    ("PART V — RUNNING THE BANK", ["chapters/ch10-for-everyone-reliability.md", "chapters/ch11-engineering-operations-manual.md"]),
    ("PART VI — WHAT WE BUILT", ["chapters/ch12-for-everyone-product-catalog.md", "chapters/ch13-engineering-service-catalog.md"]),
    ("PART VII — THE ROAD AHEAD", ["chapters/ch14-for-everyone-future-roadmap.md", "chapters/ch15-engineering-roadmap.md"]),
    ("PART VIII — ONBOARDING", ["chapters/ch16-engineer-onboarding.md"]),
    ("APPENDICES", ["appendices/app-a-glossary.md", "appendices/app-b-faq.md", "appendices/app-c-data-dictionary.md",
                    "appendices/app-d-api-reference.md", "appendices/app-e-competitive-matrix.md",
                    "appendices/app-f-analogy-atlas.md", "appendices/app-g-changelog.md",
                    "appendices/app-h-contribution.md", "appendices/app-i-onboarding-checklist.md"]),
]

lines = ["* [Welcome to the Book](README.md)", ""]
for part in PARTS:
    title, items = part
    lines.append(f"* **{title}**")
    for item in items:
        rel, _ = (item, None) if isinstance(item, str) else item
        p = ROOT / rel
        hs = headings(p)
        if not hs:
            continue
        h1 = hs[0][1]
        label = re.sub(r"^Chapter \d+ — ", "", h1)
        num = re.match(r"Chapter (\d+)", h1)
        label = (f"{int(num.group(1)):02d}. " if num else "") + label
        lines.append(f"  * [{label}]({rel})")
        for level, text in hs:
            if level == 2 and not text.startswith("Recap") and text not in ("Key Takeaways", "Frequently Asked Questions", "Where to Go Next"):
                lines.append(f"    * [{text}]({rel}#{slugify(text)})")
    lines.append("")
(ROOT / "_sidebar.md").write_text("\n".join(lines))
print("wrote _sidebar.md")
