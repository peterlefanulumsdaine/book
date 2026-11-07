#!/bin/sh
# Build hott-epub.epub with tex4ebook. See EPUB_NOTES.md.
set -e
cd "$(dirname "$0")"
export PATH=/Library/TeX/texbin:$PATH
export LIBGS=${LIBGS:-/opt/homebrew/lib/libgs.dylib}
make version.tex >/dev/null
# The first TeX pass would otherwise read a stale index from a previous build.
rm -f hott-epub.ind
python3 epub/script-macros.py macros.tex > hott-epub-macros.tex
tex4ebook -f epub3 -c hott-epub.cfg -e hott-epub.mk4 "$@" hott-epub.tex mathml
python3 -I epub/postprocess.py hott-epub-epub3 hott-epub.epub
