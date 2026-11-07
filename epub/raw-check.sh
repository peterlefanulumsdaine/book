#!/bin/sh
# Re-run tex4ht's DVI-to-XHTML step on the last build into a scratch directory
# (before make4ht/tex4ebook filters rewrite the files) and report the first
# well-formedness error in each file. Prints the scratch directory path last.
set -e
cd "$(dirname "$0")/.."
export PATH=/Library/TeX/texbin:$PATH
dir=$(mktemp -d /tmp/hott-raw.XXXX)
cp hott-epub.dvi hott-epub.tmp hott-epub.xref "$dir"/
(cd "$dir" && tex4ht -cmozhtf -utf8 hott-epub.dvi >/dev/null 2>&1)
for f in "$dir"/*.xhtml; do
  xmllint --noout "$f" 2>&1 | head -1
done
echo "$dir"
