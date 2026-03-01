# OpenHands Fast Stack (SuperAGI Workspace)

This workspace now includes a **fast-path coding agent stack**:
- OpenHands (coding agent UI + runtime)
- Docker sandbox runtime (via OpenHands runtime image)
- LiteLLM gateway (already present in companions)
- Optional SearXNG search backend
- Optional framework repos (LangGraph, AutoGen) as disabled-by-default externals

## What was added
- `external-projects.json`
  - `openhands` enabled
  - `langgraph` disabled
  - `autogen` disabled
- `docker-compose.companions.yml`
  - `companion_openhands`
  - `companion_searxng`
- `config_template.yaml`
  - `OPENHANDS_URL` and `SEARXNG_URL` placeholders

## 1) Sync external repos
From the repo root (PowerShell):

```powershell
./scripts/sync-external-projects.ps1 -Action init
```

To also pull optional framework repos:
1. Edit `external-projects.json`
2. Set `langgraph.enabled` and/or `autogen.enabled` to `true`
3. Run sync again

## 2) Set your model keys
OpenHands is pointed at LiteLLM (`http://companion_litellm:4000/v1`) by default.

Set at least one provider key in your shell or `.env` used by Docker Compose:
- `OPENAI_API_KEY` (or other provider keys consumed by your `litellm.config.yaml`)
- Optional: `LITELLM_MASTER_KEY` (defaults to `sk-local`)

## 3) Start the stack

```powershell
docker compose -f docker-compose.yaml -f docker-compose.companions.yml --profile companions up -d --build
```

## 4) Open endpoints
- SuperAGI: http://localhost:3000
- LiteLLM: http://localhost:4000
- OpenHands: http://localhost:3001
- SearXNG: http://localhost:8088

## Notes
- OpenHands uses Docker socket + `./workspace` mount for sandboxed execution.
- If you want stricter isolation, run OpenHands on a dedicated VM host and keep only API-level access back to this stack.
- Reverse engineering tools are **not** auto-installed here; keep those in an isolated lab VM for authorized use only.
