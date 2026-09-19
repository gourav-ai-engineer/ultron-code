# Screen and UI Fallback

ULTRON CODE supports a UI fallback when an official provider API cannot expose the state needed by the workflow.

## Observation

The screen observer:

1. focuses a configured desktop window
2. captures a screenshot
3. optionally runs OCR through Tesseract
4. converts visible text into the same `ProviderSnapshot` contract used by API adapters

This means API and UI observations feed the same correlation and decision pipeline.

## Interaction

The desktop interaction adapter can:

1. focus the configured window
2. type the synthesized prompt
3. press the configured submit key

Prompt delivery requires:

- `ULTRON_AUTOMATION_ENABLED=true`
- an explicit approved `ApprovalRequest`
- a matching workflow correlation ID

## OCR dependencies

Install the optional Python dependencies:

`pip install -e ".[automation,ocr]"`

Tesseract itself must also be installed on the machine and, when it is not on PATH, configured with `ULTRON_TESSERACT_CMD`.

## Safety

The UI path is intentionally a fallback. It is disabled by default and remains behind the existing approval, safety, and audit boundaries.
