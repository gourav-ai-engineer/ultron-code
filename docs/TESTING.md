# ULTRON Verification

The implementation pass is complete. Verification is intentionally a separate step.

## Local checks

Install development dependencies:

`python -m pip install -e ".[dev,api]"`

Run lint:

`ruff check .`

Run type checking:

`mypy src`

Run tests:

`pytest -q`

Run the CLI help:

`ultron --help`

Run a safe offline workflow:

`ultron workflow-run --provider mock --provider-summary "Working" --progress 0.5`

## Desktop verification

For screen/OCR verification install:

`python -m pip install -e ".[automation,ocr]"`

Ensure Tesseract is installed and available.

Then configure:

`ULTRON_AUTOMATION_ENABLED=true`

Use:

`ultron provider-status --provider screen-chatgpt --screen-window-title "ChatGPT"`

Do not enable autonomous dispatch until the observation and prompt-delivery path has been manually verified.

## CI

The repository contains a GitHub Actions matrix for Python 3.11, 3.12, 3.13, and 3.14.

CI performs:

- dependency installation
- Ruff
- MyPy
- Pytest

These checks have not been executed during the implementation pass.
