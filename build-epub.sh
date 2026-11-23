#!/bin/sh
# Build hott-epub.epub with tex4ebook. See EPUB_NOTES.md.
# All intermediate files go in build/epub/ (safe to delete); only the final
# hott-epub.epub is written to the repository root.
set -e
root=$(cd "$(dirname "$0")" && pwd)
cd "$root"
export PATH=/Library/TeX/texbin:$PATH
export LIBGS=${LIBGS:-/opt/homebrew/lib/libgs.dylib}
make version.tex >/dev/null
# Start from a clean directory, so no stale .ind/.aux etc. can be picked up.
rm -rf build/epub
mkdir -p build/epub
# TeX, BibTeX and makeindex run in build/epub but find the sources, images,
# .bst and .ist in the repository root.
export TEXINPUTS=".:$root:"
export BIBINPUTS=".:$root:"
export BSTINPUTS=".:$root:"
export INDEXSTYLE=".:$root:"
cd build/epub
python3 "$root/epub/script-macros.py" "$root/macros.tex" > hott-epub-macros.tex
tex4ebook -f epub3 -c "$root/hott-epub.cfg" -e "$root/hott-epub.mk4" "$@" \
  "$root/hott-epub.tex" mathml
python3 -I "$root/epub/postprocess.py" hott-epub-epub3 "$root/hott-epub.epub"
