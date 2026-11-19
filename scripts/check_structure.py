#!/usr/bin/env python3
"""Structure checker for the Riverbrand Knowledge Book.

Checks (default mode):
  1. Expected file set exists (front matter f01-f07, chapters ch01-ch16, appendices app-a..app-i)
  2. Chapter filename number == in-document `# Chapter N` heading == sidebar label
  3. Section numbering inside each chapter matches the chapter number (N.M)
  4. Every heading slug is ASCII-safe ([a-z0-9-]+)
  5. No duplicate headings within a file
  6. Every relative markdown link and #anchor resolves
  7. Word-count floors per chapter class
  8. Banned hype words absent (evidence-over-hype standard)
  9. Jargon leak check: non-technical chapters must not contain table/column/job names

Usage:
  scripts/check-structure.sh              # run all checks
  scripts/check-structure.sh --toc        # print a TOC generated from live headings
  scripts/check-structure.sh --no-wordcount   # skip word-count floors (skeleton phase)
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CHAPTER_MIN_WORDS = {
    # foundations + onboarding
    **{n: 2500 for n in (1, 2, 3, 16)},
    # non-technical twins
    **{n: 2800 for n in (4, 6, 8, 10, 12, 14)},
    # technical twins
    **{n: 3500 for n in (5, 7, 9, 11, 13, 15)},
}

NONTECH_CHAPTERS = {4, 6, 8, 10, 12, 14}

HYPE_WORDS = [
    r"bulletproof",
    r"absolute (mathematical )?guarantee",
    r"military-grade",
    r"unbreakable",
    r"100% (secure|safe|uptime)",
]

# Implementation identifiers that must never appear in non-technical chapters.
JARGON_PATTERNS = [
    r"rbp_brand_",
    r"river_brand_",
    r"jwt_version",
    r"prisma\.\$transaction",
    r"FOR UPDATE SKIP LOCKED",
    r"\.ts`",
    r"x-local-access-token",
    r"x-web-access-token",
    r"KycTierUpgradedHandler",
]

EXPECTED_CHAPTERS = list(range(1, 17))
EXPECTED_FRONT = ["f01-title-page", "f02-authors", "f03-copyright", "f04-preface",
                  "f05-how-to-read", "f06-table-of-contents", "f07-list-of-figures"]
EXPECTED_APPENDICES = ["app-a-glossary", "app-b-faq", "app-c-data-dictionary",
                       "app-d-api-reference", "app-e-competitive-matrix",
                       "app-f-analogy-atlas", "app-g-changelog", "app-h-contribution",
                       "app-i-onboarding-checklist"]

errors = []
warnings = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def slugify(heading: str) -> str:
    """Mirror docsify-style slug: keep ascii alnum, spaces -> hyphens."""
    h = heading.strip()
    h = re.sub(r"[`*_]", "", h)           # strip inline markup
    h = h.lower()
    h = re.sub(r"[^a-z0-9 \-]", "", h)   # drop punctuation/emoji/unicode
    h = re.sub(r"\s+", "-", h.strip())
    h = re.sub(r"-+", "-", h).strip("-")
    return h


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def parse_file(path: Path):
    headings = []  # (level, text, slug, line_no)
    text = path.read_text(encoding="utf-8")
    in_code = False
    for i, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = HEADING_RE.match(line)
        if m:
            level = len(m.group(1))
            raw = m.group(2).strip()
            headings.append((level, raw, slugify(raw), i))
    return text, headings


def chapter_number_from_name(path: Path):
    m = re.match(r"ch(\d+)-", path.name)
    return int(m.group(1)) if m else None


def check_expected_files():
    for name in EXPECTED_FRONT:
        p = ROOT / "front-matter" / f"{name}.md"
        if not p.exists():
            err(f"missing front-matter/{name}.md")
    for n in EXPECTED_CHAPTERS:
        matches = list((ROOT / "chapters").glob(f"ch{n:02d}-*.md")) if (ROOT / "chapters").exists() else []
        if not matches:
            err(f"missing chapters/ch{n:02d}-*.md")
    for name in EXPECTED_APPENDICES:
        p = ROOT / "appendices" / f"{name}.md"
        if not p.exists():
            err(f"missing appendices/{name}.md")


def check_chapter_identity(path: Path, text: str, headings):
    n = chapter_number_from_name(path)
    if n is None:
        err(f"{path.name}: filename does not start with chNN-")
        return None
    h1s = [h for h in headings if h[0] == 1]
    if not h1s:
        err(f"{path.name}: no H1 heading")
        return n
    h1 = h1s[0][1]
    m = re.match(r"Chapter\s+(\d+)\b", h1)
    if not m:
        err(f"{path.name}: H1 '{h1}' does not start with 'Chapter N'")
    elif int(m.group(1)) != n:
        err(f"{path.name}: H1 says Chapter {m.group(1)} but filename says ch{n:02d}")
    # section numbering must match chapter number
    for level, raw, slug, ln in headings:
        if level != 2:
            continue
        sm = re.match(r"(\d+)\.(\d+)\s", raw)
        if sm and int(sm.group(1)) != n:
            err(f"{path.name}:{ln}: section '{raw}' numbered {sm.group(1)}.x but chapter is {n}")
        # duplicate-numbered H2 (e.g. two 7.8)
    seen_nums = {}
    for level, raw, slug, ln in headings:
        if level == 2:
            sm = re.match(r"(\d+\.\d+)\s", raw)
            if sm:
                if sm.group(1) in seen_nums:
                    err(f"{path.name}: duplicate section number {sm.group(1)} (lines {seen_nums[sm.group(1)]} and {ln})")
                seen_nums[sm.group(1)] = ln
    return n


def check_slugs(path: Path, headings):
    for level, raw, slug, ln in headings:
        if not slug:
            err(f"{path.name}:{ln}: heading '{raw}' produces an empty slug")
        elif not re.fullmatch(r"[a-z0-9\-]+", slug):
            err(f"{path.name}:{ln}: heading '{raw}' slug '{slug}' is not ASCII-safe")


def check_duplicate_headings(path: Path, headings):
    seen = {}
    for level, raw, slug, ln in headings:
        key = (level, slug)
        if key in seen:
            warn(f"{path.name}: duplicate heading '{raw}' (lines {seen[key]} and {ln})")
        seen[key] = ln


def collect_all_headings():
    """Map of file relpath -> {slug} and 'file' -> exists."""
    index = {}
    files = []
    for sub in ("front-matter", "chapters", "appendices"):
        d = ROOT / sub
        if d.exists():
            files.extend(sorted(d.glob("*.md")))
    for p in files:
        _, headings = parse_file(p)
        index[str(p.relative_to(ROOT))] = {h[2] for h in headings}
    return index, files


def check_links(files, index):
    for p in files:
        text, _ = parse_file(p)
        in_code = False
        for i, line in enumerate(text.splitlines(), 1):
            if line.strip().startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                continue
            for target in LINK_RE.findall(line):
                if target.startswith(("http://", "https://", "mailto:")):
                    continue
                if target.startswith("#"):
                    anchor = target[1:]
                    if anchor not in index[str(p.relative_to(ROOT))]:
                        err(f"{p.name}:{i}: anchor {target} not found in this file")
                    continue
                if "#" in target:
                    rel, anchor = target.split("#", 1)
                else:
                    rel, anchor = target, None
                if rel.startswith("/"):
                    dest = (ROOT / rel.lstrip("/")).resolve()
                else:
                    dest = (p.parent / rel).resolve()
                rel_dest = None
                try:
                    rel_dest = str(dest.relative_to(ROOT))
                except ValueError:
                    pass
                if not dest.exists():
                    err(f"{p.name}:{i}: link target '{target}' does not exist")
                elif anchor and rel_dest in index:
                    if anchor not in index[rel_dest]:
                        err(f"{p.name}:{i}: anchor #{anchor} not found in {rel}")


def check_word_counts(chapter_files):
    for p in chapter_files:
        n = chapter_number_from_name(p)
        if n is None or n not in CHAPTER_MIN_WORDS:
            continue
        words = len(p.read_text(encoding="utf-8").split())
        floor = CHAPTER_MIN_WORDS[n]
        if words < floor:
            err(f"{p.name}: {words} words < floor {floor} ({'non-technical' if n in NONTECH_CHAPTERS else 'technical/foundation'} chapter)")


def check_tone(files):
    for p in files:
        text, _ = parse_file(p)
        for pat in HYPE_WORDS:
            for m in re.finditer(pat, text, re.IGNORECASE):
                line_no = text[: m.start()].count("\n") + 1
                err(f"{p.name}:{line_no}: banned hype phrase '{m.group(0)}'")


def check_jargon(files):
    for p in files:
        n = chapter_number_from_name(p)
        if n not in NONTECH_CHAPTERS:
            continue
        text, _ = parse_file(p)
        for pat in JARGON_PATTERNS:
            for m in re.finditer(pat, text):
                line_no = text[: m.start()].count("\n") + 1
                err(f"{p.name}:{line_no}: implementation jargon '{m.group(0)}' in non-technical chapter")


def check_sidebar(files):
    sidebar = ROOT / "_sidebar.md"
    if not sidebar.exists():
        err("missing _sidebar.md")
        return
    sb = sidebar.read_text(encoding="utf-8")
    for p in files:
        rel = str(p.relative_to(ROOT))
        if rel not in sb:
            err(f"_sidebar.md: missing entry for {rel}")
    # chapter labels must carry the right number
    for p in files:
        n = chapter_number_from_name(p)
        if n is None:
            continue
        rel = str(p.relative_to(ROOT))
        for line in sb.splitlines():
            if rel in line:
                # label is the markdown link text
                m = re.search(r"\[([^\]]+)\]", line)
                if m and not re.search(rf"\b0?{n}\b", m.group(1)):
                    err(f"_sidebar.md: entry for {rel} label '{m.group(1)}' does not carry chapter number {n}")
                break


def print_toc():
    print("# Table of Contents")
    print()
    print("*The full book, to section level. Regenerate with `make toc`.*")
    print()
    parts = [("front-matter", EXPECTED_FRONT), ("chapters", None), ("appendices", EXPECTED_APPENDICES)]
    for sub, names in parts:
        d = ROOT / sub
        if not d.exists():
            continue
        files = sorted(d.glob("*.md")) if names is None else [d / f"{n}.md" for n in names]
        for p in files:
            if not p.exists():
                continue
            _, headings = parse_file(p)
            # Links are emitted relative to front-matter/f06-table-of-contents.md so they
            # resolve on GitHub Pages project sites (never root-absolute).
            rel = f"../{sub}/{p.name}" if sub != "front-matter" else p.name
            for level, raw, slug, ln in headings:
                if level <= 3:
                    indent = "  " * (level - 1)
                    print(f"{indent}- [{raw}]({rel}#{slug})")


def main():
    args = set(sys.argv[1:])
    if "--toc" in args:
        print_toc()
        return 0

    check_expected_files()
    index, files = collect_all_headings()
    chapter_files = sorted((ROOT / "chapters").glob("ch*.md")) if (ROOT / "chapters").exists() else []

    for p in chapter_files:
        text, headings = parse_file(p)
        check_chapter_identity(p, text, headings)
    for p in files:
        _, headings = parse_file(p)
        check_slugs(p, headings)
        check_duplicate_headings(p, headings)
    check_links(files, index)
    if "--no-wordcount" not in args:
        check_word_counts(chapter_files)
    check_tone(files)
    check_jargon(files)
    check_sidebar(files)

    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
