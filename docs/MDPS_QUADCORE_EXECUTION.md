# MDPS-QUADCore Execution Plan

This is the current executable path for your target architecture:

- vLLM for local inference (including vision-capable model)
- chart image color/market-bias analysis
- payload handoff to Omnicore
- multi-engine Docker runtime

## What Is Implemented In This Repo

- Companion stack compose file with optional `companion_vllm` service:
  - `docker-compose.companions.yml`
- Chart analysis toolkit:
  - `superagi/tools/chart_analysis/chart_analysis_toolkit.py`
  - `superagi/tools/chart_analysis/chart_color_signal.py`
  - `superagi/tools/chart_analysis/chart_structure_vision.py`
- Omnicore bridge config keys in `config_template.yaml`:
  - `OMNICORE_WEBHOOK_URL`
  - `OMNICORE_API_KEY`
  - `OMNICORE_TIMEOUT_SECONDS`

## Current Limit

- Vision parsing is model-driven and depends on your selected vLLM/OpenAI-compatible model quality.
- No deterministic CV candle parser is included yet.

## Run Order

1. Configure `config.yaml` from `config_template.yaml`.
2. Set model provider base:
   - `OPENAI_API_BASE: "http://companion_vllm:8000/v1"` for direct vLLM
   - or keep LiteLLM and route to vLLM through LiteLLM config.
3. Configure Omnicore endpoint:
   - `OMNICORE_WEBHOOK_URL`
   - `OMNICORE_API_KEY` (if required)
4. Start services:
   - `docker compose -f docker-compose.yaml -f docker-compose.companions.yml --profile companions up --build`
5. In SuperAGI UI, enable `Chart Analysis Toolkit` on the agent.
6. Provide an image file and invoke:
   - `ChartStructureVision` for structured chart interpretation JSON.
   - `ChartColorSignal` for color-bias signal + Omnicore handoff.

## Payload Sent To Omnicore

`ChartColorSignal` sends JSON with:

- `timestamp_utc`
- `chart_file_name`
- `analysis.signal` (`bullish|bearish|neutral`)
- `analysis.confidence`
- `analysis.dominant_colors[]`

## Next Upgrade Steps (Recommended)

1. Fuse color signal + vision structure into one execution-level signal object.
2. Add risk layer before Omnicore dispatch (min confidence, spread/slippage filters).
3. Add backtest harness for signal quality against historical chart sets.
4. Add deterministic CV augmenters (axis/OHLC extraction, pattern checks) for validation.
