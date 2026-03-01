# Chart Analysis Toolkit

This toolkit adds chart-image analysis for trading workflows:

- Extracts dominant colors from a chart image.
- Infers a simple market bias (`bullish`, `bearish`, `neutral`) from green/red color density.
- Parses chart structure with an OpenAI-compatible vision model (vLLM/OpenAI/LiteLLM).
- Writes a JSON analysis report to resource output.
- Optionally forwards the payload to Omnicore via webhook.

## Tool

- `ChartColorSignal`
- `ChartStructureVision`

## Required Inputs

- `chart_file_name`: image file in agent resources (input or output path).

## Optional Config

- `OMNICORE_WEBHOOK_URL`: webhook endpoint to receive analysis payload.
- `OMNICORE_API_KEY`: bearer token added to `Authorization` header.
- `OMNICORE_TIMEOUT_SECONDS`: request timeout for webhook post.

## Notes

- This is color-bias analysis, not full candle/OHLC parsing.
- `ChartStructureVision` provides model-driven structural interpretation with strict JSON prompting.
