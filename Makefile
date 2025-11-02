.PHONY: run dev build install clean test

# Run the application in menu bar mode
run:
	python -m smile_volume

# Run in development/CLI mode
dev:
	python -m smile_volume --no-menubar

# Run calibration
calibrate:
	python -m smile_volume --calibrate

# Install dependencies
install:
	pip install -e .

# Install with dev dependencies
install-dev:
	pip install -e ".[dev]"

# Build standalone app with PyInstaller
build: install-dev
	@echo "Building standalone macOS app..."
	pyinstaller --onefile --windowed \
		--name SmileVolume \
		smile_volume/__main__.py
	@echo "✅ Build complete: dist/SmileVolume"

# Clean build artifacts
clean:
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Run tests (if available)
test:
	pytest tests/ -v

# Show configuration
config:
	@echo "Config location: ~/Library/Application Support/SmileVolume/config.json"
	@cat ~/Library/Application\ Support/SmileVolume/config.json 2>/dev/null || echo "No config file found (run app first)"

# Reset configuration
reset-config:
	rm -rf ~/Library/Application\ Support/SmileVolume/
	@echo "✅ Configuration reset"
