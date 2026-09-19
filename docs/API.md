# ULTRON HTTP API

The optional API exposes the local ULTRON runtime for a dashboard or another trusted local client.

## Install

`pip install -e ".[api]"`

FastAPI is pinned to a current 0.141.x release range in the optional API dependency because FastAPI itself recommends pinning versions in production. https://fastapi.tiangolo.com/deployment/versions/ citeturn459542search3

## Endpoints

- `GET /health`
- `GET /providers`
- `GET /runs`
- `GET /runs/latest`
- `POST /runs/observe`

The API defaults to the loopback address through `UltronSettings.api_host`. It is intended for a trusted local control plane; authentication and reverse-proxy protection should be added before exposing it beyond the local machine.

## Safety

The API can trigger observations. It does not expose a generic shell or bypass the approval and execution layers. The `POST /runs/observe` endpoint is observation-only.

For local development, the FastAPI ecosystem supports a development server through its CLI. https://fastapi.tiangolo.com/tutorial/first-steps/ citeturn459542search4
