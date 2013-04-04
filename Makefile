all: main.pdf

main.pdf: *.tex cover.png
	if which latexmk > /dev/null ;\
	then latexmk -pdf main.tex ;\
	else pdflatex main.tex && \
	     bibtex main && \
	     pdflatex main.tex ;\
	fi

clean:
	(which latexmk && latexmk -c main.tex) || /bin/rm -f main.{out,log,pdf,fls,fdb_latexmk}

# list the tex files explicitly because:
#   - we want to tag them in the same order they appear in the book, so tag search is in logical sequence
#   - there are many *.tex garbage files in this directory
TAGS: main.tex macros.tex front.tex preface.tex introduction.tex preliminaries.tex basics.tex basics-equivalences.tex\
	computational.tex equivalences.tex induction.tex hits.tex hlevels.tex homotopy.tex categories.tex \
	setmath.tex ordcard.tex reals.tex uatofe.tex formal.tex
	etags $^ >TAGS
