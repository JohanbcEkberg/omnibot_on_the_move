PYTHON ?= python3

.PHONY: help check-deps run install-deps

help:
	@echo "Available targets:"
	@echo "  make check-deps   Check required Python dependencies"
	@echo "  make run          Check dependencies and run main.py"

check-deps:
	@$(PYTHON) -c "import tkinter" || (echo "Missing dependency: tkinter" && echo "Install Python with Tk support" && exit 1)
	@$(PYTHON) -c "import requests" || (echo "Missing dependency: requests" && echo "Install with: \`pip install requests\`" && exit 1)
	@echo "All required dependencies are installed."

run: check-deps
	@$(PYTHON) main.py
