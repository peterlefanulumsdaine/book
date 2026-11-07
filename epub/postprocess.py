#!/usr/bin/env python3
"""Final fixes on tex4ebook's unpacked EPUB, then re-zip it.

These run after all make4ht/tex4ebook filters, so they see the final markup.

Usage: postprocess.py hott-epub-epub3 hott-epub.epub
"""
import pathlib
import re
import sys
import zipfile

FIXES = [
    # make4ht's mathmlfixes DOM filter adds an empty rowlines attribute to
    # every aligned environment without horizontal rules; empty is invalid.
    (re.compile(r"""\s+rowlines=(['"])\1"""), ""),
]


IMG_SVG = re.compile(r"""<img\b[^>]*?\bsrc=(['"])(hott-epub\d+x\.svg)\1[^>]*?/>""")
ALT = re.compile(r"""\balt=(['"])(.*?)\1""", re.S)
PAGE_BACKGROUND = re.compile(r"""(<g id='page1'[^>]*>\s*)<rect [^>]*fill='#fff'/>\s*""")


def inline_svg(oebps, name, alt):
    """Return the SVG `name` as inline markup that follows the text colour.

    Diagrams as <img> can't inherit the reader's text colour, and Apple Books'
    night themes ignored both prefers-color-scheme and its own theme
    attribute, leaving black-on-white boxes. Inline, with black drawn as
    currentColor, they follow whatever theme is active.
    """
    svg = (oebps / name).read_text(encoding="utf-8")
    svg = re.sub(r"<\?xml.*?\?>\s*", "", svg)
    svg = re.sub(r"<!--.*?-->\s*", "", svg, flags=re.S)
    # dvisvgm paints main.tex's \pagecolor{white} as a white rect, the first
    # child of its page group.
    svg = PAGE_BACKGROUND.sub(r"\1", svg)
    # Glyph ids (g51-72, ...) repeat across files; make them unique per page.
    prefix = name.removesuffix(".svg") + "-"
    svg = re.sub(r"""\bid='([^']+)'""", rf"id='{prefix}\1'", svg)
    svg = re.sub(r"""href='#([^']+)'""", rf"href='#{prefix}\1'", svg)
    svg = re.sub(r"url\(#([^)]+)\)", rf"url(#{prefix}\1)", svg)
    svg = svg.replace("stroke='#000'", "stroke='currentColor'")
    svg = svg.replace("fill='#000'", "fill='currentColor'")
    # Unattributed paths and glyphs default to black; inherit from the root.
    label = alt.replace("'", "&#39;")
    svg = svg.replace("<svg ", f"<svg fill='currentColor' role='img' aria-label='{label}' class='diagram' ", 1)
    return svg.strip()


def fix_xhtml(path, inlined):
    text = path.read_text(encoding="utf-8")
    new = text
    for pattern, repl in FIXES:
        new = pattern.sub(repl, new)

    def repl(m):
        alt = ALT.search(m.group(0))
        inlined.add(m.group(2))
        return inline_svg(path.parent, m.group(2), " ".join(alt.group(2).split()) if alt else "")

    new = IMG_SVG.sub(repl, new)
    if new != text:
        path.write_text(new, encoding="utf-8")
    return "<svg" in new


def fix_opf(opf, svg_docs, inlined):
    """Declare inline SVG on content documents; drop inlined SVG files."""
    text = opf.read_text(encoding="utf-8")

    def item(m):
        tag = m.group(0)
        href = re.search(r"""href=['"]([^'"]+)['"]""", tag).group(1)
        if href in inlined:
            return ""
        if href in svg_docs:
            if re.search(r"""properties=['"]""", tag):
                tag = re.sub(r"""properties=(['"])""", r"properties=\1svg ", tag, count=1)
            else:
                tag = tag.replace("<item ", "<item properties='svg' ", 1)
        return tag

    text = re.sub(r"<item\b[^>]*?(?:/>|></item>)\s*", item, text)
    opf.write_text(text, encoding="utf-8")


def rezip(src, out):
    out.unlink(missing_ok=True)
    with zipfile.ZipFile(out, "w") as z:
        # The mimetype entry must come first and be stored uncompressed.
        z.write(src / "mimetype", "mimetype", compress_type=zipfile.ZIP_STORED)
        for path in sorted(src.rglob("*")):
            rel = path.relative_to(src).as_posix()
            # tex4ebook leaves its own copy of the .epub in this directory.
            if path.is_file() and rel != "mimetype" and path.suffix != ".epub":
                z.write(path, rel, compress_type=zipfile.ZIP_DEFLATED)


def main():
    src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    oebps = src / "OEBPS"
    inlined, svg_docs = set(), set()
    for path in oebps.glob("*.xhtml"):
        if fix_xhtml(path, inlined):
            svg_docs.add(path.name)
    fix_opf(oebps / "content.opf", svg_docs, inlined)
    for name in inlined:
        (oebps / name).unlink()
    rezip(src, out)


if __name__ == "__main__":
    main()
