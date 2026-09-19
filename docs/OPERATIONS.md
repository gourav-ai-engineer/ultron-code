# ULTRON Operations

## Safe startup

Core installation:

`python -m pip install -e ".[dev]"`

Optional API:

`python -m pip install -e ".[api]"`

Optional desktop/OCR:

`python -m pip install -e ".[automation,ocr]"`

Start with:

`ultron status`

Safe defaults are:

- dry-run enabled
- desktop automation disabled
- autonomous prompt dispatch disabled

## First project

`ultron init`

`ultron plan`

`ultron next-phase`

`ultron workflow-run --provider mock --provider-summary "Working" --progress 0.5`

Inspect a persisted run:

`ultron run-show --run-id <run-id>`

## Provider observation

API-backed:

`ultron provider-status --provider chatgpt --response-id <response-id>`

`ultron provider-status --provider claude`

`ultron provider-status --provider cursor --agent-id <agent-id> --provider-run-id <run-id>`

Screen-backed:

`ultron provider-status --provider screen-chatgpt --workspace . --screen-window-title "ChatGPT"`

The screen path requires PyAutoGUI, Pillow, pytesseract, and the Tesseract executable.

## Human-approved prompt delivery

Generate a workflow run:

`ultron workflow-run --provider screen-chatgpt --screen-window-title "ChatGPT"`

Create an approval:

`ultron approval-request --action "send prompt" --rationale "Continue the active implementation" --correlation-id <run-id>`

Approve it:

`ultron approval-resolve --request-id <request-id> --status approved`

Deliver it:

`ultron prompt-send --run-id <run-id> --provider chatgpt --window-title "ChatGPT" --approval-id <request-id>`

## Autonomous desktop mode

This is intentionally opt-in.

Set:

`ULTRON_DRY_RUN=false`

`ULTRON_AUTOMATION_ENABLED=true`

`ULTRON_AUTO_PROMPT_ENABLED=true`

Then:

`ultron auto-loop --provider screen-chatgpt --screen-window-title "ChatGPT"`

Only decisions that do not require human input are automatically dispatched.

## Operator controls

Check state:

`ultron control-status`

Pause:

`ultron control-pause`

Emergency stop:

`ultron control-stop`

Resume:

`ultron control-resume`

Clear all stop/pause state:

`ultron control-clear`

The emergency stop is persistent and takes precedence over loop execution.

## API

Start:

`ultron serve`

Default endpoint:

`http://127.0.0.1:8765`

The API may be protected with `ULTRON_API_TOKEN`.

## Persistence

Runtime files live below `.ultron/` by default:

- `project.json`
- `approvals.json`
- `audit.jsonl`
- `runs.jsonl`
- `control.json`

Screen captures are removed after OCR unless retention is explicitly enabled in code.

## Recovery

`RunStore` can rehydrate a workflow by run ID.

`RecoveryManager` respects pause and emergency-stop state before resumption.

## Verification

The repository contains unit and integration tests plus CI configuration. They are intentionally not executed during the implementation pass; run the documented test commands after the entire project is assembled.
