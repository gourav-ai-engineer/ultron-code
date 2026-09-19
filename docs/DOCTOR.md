# ULTRON Doctor

`ultron doctor` performs non-mutating environment diagnostics.

It checks:

- supported Python version
- workspace availability
- Git availability
- configuration path confinement
- optional FastAPI dependency
- optional PyAutoGUI dependency
- Pillow/pytesseract availability
- Tesseract executable availability
- provider API-key presence

Provider keys are reported only as `configured` or `not configured`; their values are never displayed.

A provider key is optional unless that provider is selected.

The command does not install packages, start processes, send prompts, or modify the workspace.
