# EPUB build — working notes

Personal fork (`mglst/hott-book`, branch `epub`) of https://github.com/HoTT/book.
Goal: a reflowable EPUB3 of the HoTT book for **personal reading** on a commute
and **in the dark with dark mode**. Not upstreaming for now (no issue comments, no PRs).

## Background: upstream issue #287 ("epub or mobi version", opened 2013-06-21)

- Oldest open issue in HoTT/book. Read it with
  `gh issue view 287 -R HoTT/book --json body,comments`.
- 2013: loopspace (Andrew Stacey) built an EPUB3 + MathML + embedded STIX fonts
  using his own LaTeX class (https://github.com/loopspace/book, needs
  https://github.com/loopspace/latex-to-internet, lualatex). He got the text,
  formal.tex (mathpar), tables, the bibliography and both indexes working.
  **tikz/xymatrix figures were never done.** Reader MathML support was poor in 2013.
- Lessons from that thread worth reusing:
  - Some `equation` environments contain only text (e.g. preliminaries.tex
    `eq:tautology1`); they need a text-mode treatment.
  - Index entries link to *page numbers* in the PDF. In the EPUB, use the enclosing
    section/definition reference instead (consensus reached in the thread).
  - Underscores in labels caused trouble for converters.
  - Coloured table (homotopy groups of spheres) needs CSS.
- 2021: people suggested `tex4ebook` (make4ht/tex4ht), which has improved a lot.

## Source facts (measured)

- About 31k lines of .tex; `main.tex` is the root; `macros.tex` is 816 lines with
  about 410 `\newcommand`/`\def`.
- About 55 tikzpicture, about 71 `\xymatrix`, `mathpar` in formal.tex.
- Variant entry points: `hott-online.tex`, `hott-ebook*.tex`, `opt-*.tex` option files.

## Chosen approach

- Toolchain: **tex4ebook** (runs real TeX, so the custom macros just work; tikz/xymatrix
  become SVG via dvisvgm). Fall back to LaTeXML only if tex4ebook hits a wall.
- Math: **MathML** (MathML Core is in WebKit/Chromium/Gecko as of 2023+;
  Apple Books and Thorium render it). MathML takes the text colour, so dark mode works.
  An SVG-math variant would only be needed for Kindle/e-ink. Not a priority.
- **Leave the book's .tex sources untouched.** Put everything in a separate config
  (`.cfg` for tex4ht, a build script, CSS).

## Dark-mode requirements (important)

- CSS must not hardcode foreground or background colours on body text; let the reader theme win.
- SVG figures from dvisvgm have black strokes by default, which are invisible on a dark
  background. Rewrite fills and strokes to `currentColor`, or use a
  `@media (prefers-color-scheme: dark)` rule. Check this in a dark-themed reader.
- Coloured elements (tables, diagrams) need colours that stay readable on both backgrounds.

## Validation

- `epubcheck` should report no errors.
- Visual QA: Apple Books (macOS) in light and dark mode; Thorium; spot-check against the PDF.

## Build pipeline (as built)

Tools: MacTeX (`/Library/TeX/texbin`), Homebrew `ghostscript` and `epubcheck`. The
user installs Homebrew packages from a separate admin account, so ask them to run
`brew install` rather than running it yourself.

`./build-epub.sh` takes about 70 s and produces `hott-epub.epub`:

1. `make version.tex`; recreate an empty `build/epub/` (all TeX/BibTeX/makeindex runs happen
   there, finding the sources in the repo root via `TEXINPUTS` etc.); generate
   `build/epub/hott-epub-macros.tex` with `epub/script-macros.py`.
2. `tex4ebook -f epub3 -c hott-epub.cfg -e hott-epub.mk4 hott-epub.tex mathml`
   (pdfTeX/DVI mode. LuaLaTeX was much worse with this preamble.)
3. `epub/postprocess.py`: final string fixes on `build/epub/hott-epub-epub3/`, then re-zip to `./hott-epub.epub`.

Files:
- `hott-epub.tex`: entry point (no cover, colour, letter options; mathpazo disabled).
- `hott-epub.cfg`: tex4ht config. Every override has a comment explaining why.
- `hott-epub.mk4`: make4ht build file (bibtex, patched makeindex, string filters).
- `hott-epub.ist`: makeindex style that emits the `\IDXP` sentinel.
- `epub/script-macros.py`: re-emits macros containing `^`/`_` (see below).
- `epub/postprocess.py`, `epub/raw-check.sh`, `epub/excerpt.py`: post-fixes, raw-output
  XML check, and standalone excerpt pages for screenshots.

## Fixes and their causes (read before changing anything)

- **Preamble macros lose sub/superscripts.** tex4ht makes `^`/`_` active at
  `\begin{document}`; macros tokenised earlier keep catcode 7/8, so `\opp`, `\idtype`
  and `\refl` came out flat. `script-macros.py` extracts the definitions containing
  `^`/`_`, and the .cfg re-reads them. It also braces `^\cmd{x}` to `^{\cmd{x}}`,
  unwraps `\mathord{..}` etc. around scripts (they otherwise produce `<mi><msup>`),
  and turns `\ensuremath{X}\xspace` into `\hottmath{X}`. The `\xspace` token sat
  between a subscript and a superscript and broke tex4ht's msubsup lookahead.
  `\hottmath` must be `\protected` (alignment cells).
- **Flat MathML after any image.** html-mml.4ht's IMG config pauses math
  classification for alt text and never resumes. The .cfg redefines IMG without the pause.
- **Diagrams invisible.** tex4ht wraps in-math images in `<semantics><annotation-xml>`,
  and MathML Core renders only the first child of `<semantics>`. The .cfg emits
  `<mtext><img/></mtext>` instead (works in Chrome and Apple Books).
- **Diagram labels misplaced** (`f(x)^{f(p)}` instead of a label on the arrow). In the
  document tex4ht gives `^`/`_` catcode 12 + mathcode "8000; xy-pic needs catcode 7/8.
  The .cfg re-tokenises every `\xymatrix` via `\scantokens` with normal catcodes.
  (`\let` on the characters can't work, and bodies inside align* are already tokenised.)
- **Diagrams in dark mode.** Apple Books ignored both `prefers-color-scheme` and the
  `__ibooks_internal_theme` attribute, which showed up as black-on-white boxes.
  `postprocess.py` inlines every diagram SVG, drawing black as `currentColor`, removes
  dvisvgm's white page-background rect (from main.tex's `\pagecolor{white}`; `\nopagecolor`
  breaks dvisvgm), prefixes glyph ids per file, and declares `properties="svg"` in the OPF.
- **Empty `\mathopen{}`/`\mathclose{}`** (spacing idiom in `\trunc`, `\pairr`, ...)
  become empty `<mo>` that swallow following elements, so the .cfg drops the empty ones.
  `\tproj` is overridden so it doesn't emit an empty `^{}` (double superscript with `\cd{A}^{..}`).
- **Input stack overflow at the first `aligned` (TeX Live 2026).** tex4ht's `colortbl.4ht`
  does `\CT@everycr{...\the\everycr}`. With array >= 2026/02/24, `\CT@everycr` *is*
  `\everycr` (no separate `\newtoks`), so the token list contains itself and TeX recurses
  until "input stack size" is exceeded (raising `stack_size` does not help). `hott-epub.tex`
  clears it with `\AtBeginDocument{\everycr{}}`; harmless on older TeX Live. Skipping
  colortbl entirely does not work (tex4ht's array support then fails on the first tabular).
- `<math>` needs `xmlns` in XHTML: `\Configure{math-xmlns}`.
- `\raisebox` → `\hbox` (calc expression in hlevels.tex; xy-pic needs live catcodes).
- `\vcenter` must **not** be redefined: tabular/aligned use it internally. A stray
  `<p>` inside display math (Definition 7.4.8) is removed by a string filter in the .mk4.
- **Index.** make4ht's .ind rewriter regex-splits term from page list and breaks on
  `^`, digits and commas in math terms. A copy of make4ht-indexing.lua is patched at
  load time to split on the `\IDXP` sentinel; its de-dup is disabled and replaced by
  `tidy_index`. Locators are section numbers (`\Configure{makeindex}`); "Intro" for the
  unnumbered introduction.
- TOC: Notes/Exercises were double-listed and Bibliography/Index were fake `part`
  entries; both broke NCX nesting. Overridden in the .cfg.
- make4ht's char table has U+207F shcode=14 (should be 110), which puts 0x0e in a section
  id. Patched in the .mk4.
- `Make:match` commands receive a *filename*; wrap string transforms with
  `require "make4ht-filter"`. Domfilters may run first; the .mk4 moves its filter to the
  front. Anything that must see final markup goes in `postprocess.py`.

## Status (2026-11-07)

- Builds cleanly; epubcheck has 91 errors left (from 41k). These are minor MathML schema issues
  (some `msub` child counts, `mover` placement, `<img>` in `<mtext>`), 4 links to the
  Appendix with undefined fragments, and an empty `<title>` on the title page.
- Known visual issues: Table 8.1's coloured cells are fixed-width boxes and don't line up
  as in the PDF. Subscripts on `\right` delimiters (e.g. ‖A‖₀ via `\trunc`) render inline,
  not as subscripts.
- Apple Books (macOS) shows text and math correctly. The inlined-SVG dark-mode fix is not yet
  confirmed on a device.

## Status (2026-11-23)

- Intermediates moved to `build/epub/` (gitignored; `rm -rf build` to clean). A from-scratch
  build exposed that the old pass sequence only worked because stale files in the source
  directory were being reused: index locators came out as `#dxNN-NNNNNN` with no file name.
  The .mk4 now runs htlatex, bibtex, htlatex, makeindex, htlatex, htlatex (see comment there).
  The resulting epub is identical to the previous one apart from date/version string.

- Builds cleanly on TeX Live 2026 after the `\everycr` fix above.
  Without it the build died with `TeX capacity exceeded [input stack size=10000]`.
- Compared with an epub built from this branch by mglst: visible text identical (apart from
  the `Book version:` string, which comes from `git describe` and so depends on local tags).
  Structural differences are benign: newer tex4ht writes `<mi mathvariant='script'>` where
  the older wrote `<mstyle mathvariant='script'><mi>`, and some multi-row `aligned` blocks
  now have extra empty trailing `<mtd columnalign='right'>` cells (e.g. 8.1.6, and the
  display at homotopy.tex ~l.2071). No visible difference in Apple Books.
