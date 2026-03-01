import base64
import json
import os
from datetime import datetime, timezone
from typing import Optional, Type

import requests
from pydantic import BaseModel, Field

from superagi.config.config import get_config
from superagi.helper.resource_helper import ResourceHelper
from superagi.lib.logger import logger
from superagi.models.agent import Agent
from superagi.models.agent_execution import AgentExecution
from superagi.resource_manager.file_manager import FileManager
from superagi.tools.base_tool import BaseTool


DEFAULT_CHART_SCHEMA_PROMPT = """Read this trading chart image and return strict JSON only with keys:
{
  "timeframe": "string",
  "trend": "up|down|sideways",
  "support_levels": [number],
  "resistance_levels": [number],
  "notable_patterns": ["string"],
  "indicator_summary": "string",
  "trade_bias": "bullish|bearish|neutral",
  "confidence": 0.0
}
Do not include markdown. Output valid JSON only."""


class ChartStructureVisionInput(BaseModel):
    chart_file_name: str = Field(..., description="Chart image file name in resources.")
    report_file_name: str = Field(
        "chart_vision_report.json",
        description="JSON report filename for parsed vision output.",
    )
    prompt: str = Field(
        DEFAULT_CHART_SCHEMA_PROMPT,
        description="Instruction prompt for the vision model. Must request strict JSON.",
    )
    model_name: Optional[str] = Field(
        None,
        description="Optional model override. Defaults to MODEL_NAME from config.",
    )
    max_tokens: int = Field(700, description="Maximum output tokens for model response.")


class ChartStructureVisionTool(BaseTool):
    name: str = "ChartStructureVision"
    description: str = "Use an OpenAI-compatible vision model (e.g. vLLM-VL) to parse chart structure into JSON."
    args_schema: Type[BaseModel] = ChartStructureVisionInput
    agent_id: int = None
    agent_execution_id: int = None
    resource_manager: Optional[FileManager] = None
    permission_required: bool = False

    def _execute(
        self,
        chart_file_name: str,
        report_file_name: str = "chart_vision_report.json",
        prompt: str = DEFAULT_CHART_SCHEMA_PROMPT,
        model_name: Optional[str] = None,
        max_tokens: int = 700,
    ):
        image_path = ResourceHelper.get_agent_read_resource_path(
            chart_file_name,
            agent=Agent.get_agent_from_id(session=self.toolkit_config.session, agent_id=self.agent_id),
            agent_execution=AgentExecution.get_agent_execution_from_id(
                session=self.toolkit_config.session, agent_execution_id=self.agent_execution_id
            ),
        )
        if image_path is None or not os.path.exists(image_path):
            raise FileNotFoundError(f"Chart file not found: {chart_file_name}")

        api_key = get_config("OPENAI_API_KEY")
        api_base = get_config("OPENAI_API_BASE", "https://api.openai.com/v1").rstrip("/")
        model = model_name or get_config("MODEL_NAME", "gpt-4o-mini")

        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("utf-8")
        image_data_url = f"data:image/png;base64,{encoded}"

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        body = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": 0,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_data_url}},
                    ],
                }
            ],
        }

        response = requests.post(f"{api_base}/chat/completions", headers=headers, json=body, timeout=60)
        response.raise_for_status()
        response_json = response.json()

        content = (
            response_json.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        parsed = self._try_parse_json(content)

        result = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "tool": self.name,
            "chart_file_name": chart_file_name,
            "model": model,
            "raw_model_output": content,
            "parsed_output": parsed,
        }

        serialized = json.dumps(result, indent=2)
        if self.resource_manager is not None:
            self.resource_manager.write_file(report_file_name, serialized)
        else:
            fallback_path = ResourceHelper.get_resource_path(report_file_name)
            os.makedirs(os.path.dirname(fallback_path), exist_ok=True)
            with open(fallback_path, "w", encoding="utf-8") as file:
                file.write(serialized)

        return {
            "report_file_name": report_file_name,
            "parsed_output": parsed,
        }

    @staticmethod
    def _try_parse_json(content: str):
        if content is None:
            return {"error": "Empty response from model."}
        content = content.strip()
        if content.startswith("```"):
            content = content.strip("`")
            content = content.replace("json", "", 1).strip()
        try:
            return json.loads(content)
        except Exception as error:
            logger.error(f"ChartStructureVision JSON parse error: {error}")
            return {"error": "Model output is not valid JSON.", "content": content}
