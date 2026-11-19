# Riverbrand Knowledge Book — build targets
# Toolchain (pandoc, typst, mmdc) lives in tools/bin and tools/node_modules/.bin.
export PATH := $(CURDIR)/tools/bin:$(CURDIR)/tools/node_modules/.bin:$(PATH)

.PHONY: verify sidebar toc lof figures pdf pdf-vol1 pdf-vol2

verify:
	./scripts/check-structure.sh

sidebar:
	python3 scripts/gen_sidebar.py

toc:
	./scripts/check-structure.sh --toc > front-matter/f06-table-of-contents.md

lof:
	python3 scripts/gen_lof.py

figures:
	python3 scripts/convert_figures.py

pdf: pdf-vol1 pdf-vol2

pdf-vol1:
	python3 print/build.py vol1

pdf-vol2:
	python3 print/build.py vol2
