#!/usr/bin/env python3
"""PDF build for the Riverbrand Knowledge Book (two volumes).

Pipeline per volume:
  1. Pre-pass: ```mermaid blocks -> rendered SVG via @mermaid-js/mermaid-cli (mmdc)
     <!-- FIGURE: file.svg | Caption --> markers -> ![Caption](../images/file.svg) when the file exists
  2. Concatenate manifest files in order with chapter page breaks
  3. pandoc (-f gfm -t typst) + typst compile -> print/riverbrand-volume-*.pdf

Usage:
  python3 print/build.py vol1 | vol2 | all
"""

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRINT = ROOT / "print"

VOLUMES = {
    "vol1": ("volume-i-technical.md", "riverbrand-volume-i-technical.pdf"),
    "vol2": ("volume-ii-non-technical.md", "riverbrand-volume-ii-non-technical.pdf"),
}


def have(tool):
    return shutil.which(tool) is not None


def render_mermaid_blocks(text: str, workdir: Path, stem: str) -> str:
    """Replace fenced mermaid blocks with images/*.svg renders (or leave as code if no mmdc)."""
    out = []
    idx = 0
    in_block = False
    buf = []
    for line in text.splitlines(keepends=True):
        if line.strip().startswith("```mermaid"):
            in_block = True
            buf = []
            continue
        if in_block and line.strip().startswith("```"):
            in_block = False
            idx += 1
            src = workdir / f"{stem}-mermaid-{idx}.mmd"
            src.write_text("".join(buf))
            dst = ROOT / "images" / f"{stem}-mermaid-{idx}.svg"
            if have("mmdc"):
                subprocess.run(
                    ["mmdc", "-i", str(src), "-o", str(dst), "-b", "transparent", "-s"],
                    check=False, capture_output=True,
                )
                if dst.exists():
                    out.append(f"![Mermaid diagram]({dst.relative_to(ROOT / 'print')})\n")
                    continue
            out.append("```mermaid\n" + "".join(buf) + "```\n")
            continue
        if in_block:
            buf.append(line)
        else:
            out.append(line)
    return "".join(out)


FIG_RE = re.compile(r"<!--\s*FIGURE:\s*(\S+)\s*\|\s*([^>]+?)\s*-->")


def resolve_figure_markers(text: str) -> str:
    def repl(m):
        fname, caption = m.group(1), m.group(2)
        img = ROOT / "images" / fname
        if img.exists():
            return f"![{caption}](../images/{fname})"
        return f"**{caption}** *(figure pending: {fname})*"
    return FIG_RE.sub(repl, text)


def build_volume(key: str):
    manifest_name, pdf_name = VOLUMES[key]
    manifest = PRINT / manifest_name
    files = [ROOT / ln.strip() for ln in manifest.read_text().splitlines()
             if ln.strip() and not ln.startswith("#")]
    missing = [f for f in files if not f.exists()]
    if missing:
        print(f"ERROR missing files: {missing}")
        return 1

    with tempfile.TemporaryDirectory() as td:
        workdir = Path(td)
        parts = []
        for f in files:
            text = f.read_text()
            stem = f.stem
            text = render_mermaid_blocks(text, workdir, stem)
            text = resolve_figure_markers(text)
            # Normalise image paths so they resolve relative to print/ where the .typ lives.
            text = text.replace("](/images/", "](../images/")
            text = text.replace("](images/", "](../images/")
            parts.append(text.strip() + "\n")
        # H1 headings already force page breaks via typst-preamble.typ.
        combined = "\n\n".join(parts)
        md_out = PRINT / f"{key}-combined.md"
        md_out.write_text(combined)

    typ_out = PRINT / f"{key}-combined.typ"
    cmd = [
        "pandoc", str(md_out), "-f", "gfm", "-t", "typst",
        "--top-level-division=chapter", "--number-sections",
        "--toc", "--toc-depth=3",
        "--resource-path", str(ROOT),
        "--include-in-header", str(PRINT / "typst-preamble.typ"),
        "-o", str(typ_out),
    ]
    if not have("pandoc"):
        print("SKIP pandoc not installed; wrote", md_out)
        return 0
    subprocess.run(cmd, check=True)
    pdf_out = PRINT / pdf_name
    if not have("typst"):
        print("SKIP typst not installed; wrote", typ_out)
        return 0
    subprocess.run(["typst", "compile", str(typ_out), str(pdf_out)], check=True)
    print("built", pdf_out)
    return 0


def main():
    args = sys.argv[1:] or ["all"]
    targets = ["vol1", "vol2"] if "all" in args else args
    rc = 0
    for t in targets:
        if t not in VOLUMES:
            print(f"unknown volume {t}")
            rc = 1
            continue
        rc |= build_volume(t)
    return rc


if __name__ == "__main__":
    sys.exit(main())
