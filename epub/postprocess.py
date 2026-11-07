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


def fix_xhtml(path):
    text = path.read_text(encoding="utf-8")
    new = text
    for pattern, repl in FIXES:
        new = pattern.sub(repl, new)
    if new != text:
        path.write_text(new, encoding="utf-8")


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
    for path in (src / "OEBPS").glob("*.xhtml"):
        fix_xhtml(path)
    rezip(src, out)


if __name__ == "__main__":
    main()
