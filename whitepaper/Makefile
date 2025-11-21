# SolanaLM Whitepaper Makefile

# Main document name (without extension)
MAIN = solanalm-whitepaper

# LaTeX compiler
LATEX = pdflatex

# Build flags
LATEXFLAGS = -interaction=nonstopmode -halt-on-error

# Output directory
OUTDIR = build

.PHONY: all clean view help

# Default target: build PDF
all: $(MAIN).pdf

# Build PDF (run twice for references/TOC)
$(MAIN).pdf: $(MAIN).tex
	@echo "Building $(MAIN).pdf..."
	$(LATEX) $(LATEXFLAGS) $(MAIN).tex
	$(LATEX) $(LATEXFLAGS) $(MAIN).tex
	@echo "Build complete: $(MAIN).pdf"

# Quick build (single pass, faster but may have broken refs)
quick:
	@echo "Quick build (single pass)..."
	$(LATEX) $(LATEXFLAGS) $(MAIN).tex

# Clean auxiliary files
clean:
	@echo "Cleaning auxiliary files..."
	rm -f $(MAIN).aux $(MAIN).log $(MAIN).out $(MAIN).toc
	rm -f $(MAIN).lof $(MAIN).lot $(MAIN).bbl $(MAIN).blg
	rm -f $(MAIN).fls $(MAIN).fdb_latexmk $(MAIN).synctex.gz
	@echo "Clean complete"

# Clean everything including PDF
distclean: clean
	@echo "Removing PDF..."
	rm -f $(MAIN).pdf
	@echo "Distclean complete"

# View PDF (Linux)
view: $(MAIN).pdf
	@if command -v xdg-open > /dev/null; then \
		xdg-open $(MAIN).pdf; \
	elif command -v evince > /dev/null; then \
		evince $(MAIN).pdf; \
	else \
		echo "No PDF viewer found. Open $(MAIN).pdf manually."; \
	fi

# Watch for changes and rebuild (requires inotify-tools)
watch:
	@echo "Watching for changes... (Ctrl+C to stop)"
	@while true; do \
		inotifywait -q -e modify $(MAIN).tex && \
		make quick; \
	done

# Help
help:
	@echo "SolanaLM Whitepaper Build System"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  all       - Build PDF (default, runs twice for TOC)"
	@echo "  quick     - Quick build (single pass)"
	@echo "  clean     - Remove auxiliary files"
	@echo "  distclean - Remove all generated files including PDF"
	@echo "  view      - Open PDF in default viewer"
	@echo "  watch     - Auto-rebuild on file changes"
	@echo "  help      - Show this help"
	@echo ""
	@echo "Requirements: pdflatex, texlive-latex-extra"
