import colorsys
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Type

import requests
from PIL import Image
from pydantic import BaseModel, Field

from superagi.helper.resource_helper import ResourceHelper
from superagi.lib.logger import logger
from superagi.models.agent import Agent
from superagi.models.agent_execution import AgentExecution
from superagi.resource_manager.file_manager import FileManager
from superagi.tools.base_tool import BaseTool


class ChartColorSignalInput(BaseModel):
    chart_file_name: str = Field(..., description="Chart image file name available in input/output resources.")
    top_n_colors: int = Field(
        5, description="Number of dominant colors to include in output. Range 3 to 10."
    )
    send_to_omnicore: bool = Field(
        True, description="When true, posts signal payload to OMNICORE_WEBHOOK_URL if configured."
    )
    report_file_name: str = Field(
        "chart_analysis_report.json",
        description="Resource output JSON filename for analysis report.",
    )


class ChartColorSignalTool(BaseTool):
    name: str = "ChartColorSignal"
    description: str = (
        "Analyze a chart image, detect dominant colors, infer bullish/bearish bias, and optionally send to Omnicore."
    )
    args_schema: Type[BaseModel] = ChartColorSignalInput
    agent_id: int = None
    agent_execution_id: int = None
    resource_manager: Optional[FileManager] = None
    permission_required: bool = False

    def _execute(
        self,
        chart_file_name: str,
        top_n_colors: int = 5,
        send_to_omnicore: bool = True,
        report_file_name: str = "chart_analysis_report.json",
    ):
        if top_n_colors < 3:
            top_n_colors = 3
        if top_n_colors > 10:
            top_n_colors = 10

        image_path = ResourceHelper.get_agent_read_resource_path(
            chart_file_name,
            agent=Agent.get_agent_from_id(session=self.toolkit_config.session, agent_id=self.agent_id),
            agent_execution=AgentExecution.get_agent_execution_from_id(
                session=self.toolkit_config.session, agent_execution_id=self.agent_execution_id
            ),
        )

        if image_path is None or not os.path.exists(image_path):
            raise FileNotFoundError(f"Chart file not found: {chart_file_name}")

        with Image.open(image_path) as image:
            analysis = self._analyze_chart_colors(image=image, top_n_colors=top_n_colors)

        payload = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "tool": self.name,
            "chart_file_name": chart_file_name,
            "analysis": analysis,
        }

        report_json = json.dumps(payload, indent=2)
        if self.resource_manager is not None:
            self.resource_manager.write_file(report_file_name, report_json)
        else:
            fallback_path = ResourceHelper.get_resource_path(report_file_name)
            os.makedirs(os.path.dirname(fallback_path), exist_ok=True)
            with open(fallback_path, "w", encoding="utf-8") as file:
                file.write(report_json)

        omnicore_response = {"sent": False, "status_code": None, "message": "OMNICORE_WEBHOOK_URL not configured."}
        if send_to_omnicore:
            omnicore_response = self._post_to_omnicore(payload)

        return {
            "signal": analysis["signal"],
            "confidence": analysis["confidence"],
            "dominant_colors": analysis["dominant_colors"],
            "report_file_name": report_file_name,
            "omnicore": omnicore_response,
        }

    def _analyze_chart_colors(self, image: Image.Image, top_n_colors: int) -> Dict[str, Any]:
        rgb = image.convert("RGB")
        rgb.thumbnail((256, 256))

        palette_size = max(top_n_colors * 3, 8)
        quantized = rgb.quantize(colors=palette_size, method=Image.MEDIANCUT)
        palette = quantized.getpalette()
        counted = quantized.getcolors()

        if not counted:
            raise ValueError("Unable to extract colors from chart image.")

        counted = sorted(counted, key=lambda item: item[0], reverse=True)
        total_pixels = sum(item[0] for item in counted)

        dominant_colors = []
        green_ratio = 0.0
        red_ratio = 0.0

        for count, color_index in counted[:top_n_colors]:
            start = color_index * 3
            red, green, blue = palette[start : start + 3]
            ratio = count / total_pixels
            hex_color = f"#{red:02x}{green:02x}{blue:02x}"

            hue, saturation, value = colorsys.rgb_to_hsv(red / 255.0, green / 255.0, blue / 255.0)
            hue_degrees = hue * 360.0
            is_colored = saturation >= 0.20 and value >= 0.15

            if is_colored and 80 <= hue_degrees <= 170:
                green_ratio += ratio
            if is_colored and (hue_degrees <= 20 or hue_degrees >= 340):
                red_ratio += ratio

            dominant_colors.append(
                {
                    "hex": hex_color,
                    "rgb": [red, green, blue],
                    "ratio": round(ratio, 4),
                    "hue": round(hue_degrees, 1),
                }
            )

        delta = green_ratio - red_ratio
        if delta > 0.08:
            signal = "bullish"
        elif delta < -0.08:
            signal = "bearish"
        else:
            signal = "neutral"

        confidence = min(abs(delta) * 2.5, 1.0)
        return {
            "signal": signal,
            "confidence": round(confidence, 4),
            "green_ratio": round(green_ratio, 4),
            "red_ratio": round(red_ratio, 4),
            "dominant_colors": dominant_colors,
        }

    def _post_to_omnicore(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        webhook_url = self.get_tool_config("OMNICORE_WEBHOOK_URL")
        if not webhook_url:
            return {"sent": False, "status_code": None, "message": "OMNICORE_WEBHOOK_URL not configured."}

        api_key = self.get_tool_config("OMNICORE_API_KEY")
        timeout_seconds = self.get_tool_config("OMNICORE_TIMEOUT_SECONDS")
        timeout_seconds = int(timeout_seconds) if timeout_seconds is not None else 15

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            response = requests.post(webhook_url, headers=headers, json=payload, timeout=timeout_seconds)
            return {
                "sent": True,
                "status_code": response.status_code,
                "message": "Signal forwarded to Omnicore.",
            }
        except Exception as error:
            logger.error(f"Failed to post chart signal to Omnicore: {error}")
            return {
                "sent": False,
                "status_code": None,
                "message": f"Error sending signal to Omnicore: {error}",
            }
