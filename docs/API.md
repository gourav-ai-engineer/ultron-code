# ULTRON HTTP API

The optional API exposes the local ULTRON runtime for a dashboard or another trusted local client.

## Install

`python -m pip install -e ".[api]"`

## Default network boundary

ULTRON binds to `127.0.0.1` by default through `UltronSettings.api_host`.

Before exposing the service outside the local machine, configure `ULTRON_API_TOKEN` and place it behind an appropriate reverse proxy/network boundary.

## Endpoints

Public:

- `GET /health`

Protected when `ULTRON_API_TOKEN` is configured:

- `GET /providers`
- `GET /runs`
- `GET /runs/latest`
- `GET /runs/{run_id}`
- `GET /control`
- `POST /control/stop`
- `POST /control/pause`
- `POST /control/resume`
- `POST /control/clear`
- `POST /runs/observe`

Observation is read-only with respect to external provider actions. The API does not expose a generic shell.

## Dashboard

The local dashboard is mounted at:

`/dashboard/`

It reads runtime health, registered providers, and the latest workflow run.

## Authentication

When `ULTRON_API_TOKEN` is set, clients send:

`Authorization: Bearer <token>`

The token is stored as a secret setting and never included in provider snapshots or audit records.

## Safety

The API delegates observation and state control to the same runtime components used by the CLI.

Execution still goes through the executor allowlist, safety policy, approval layer, and audit trail.
