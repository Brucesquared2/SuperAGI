from abc import ABC
from typing import List

from superagi.tools.base_tool import BaseTool, BaseToolkit, ToolConfiguration
from superagi.tools.chart_analysis.chart_color_signal import ChartColorSignalTool
from superagi.tools.chart_analysis.chart_structure_vision import ChartStructureVisionTool
from superagi.types.key_type import ToolConfigKeyType


class ChartAnalysisToolkit(BaseToolkit, ABC):
    name: str = "Chart Analysis Toolkit"
    description: str = "Analyze chart images, extract color bias, and optionally forward a signal to Omnicore."

    def get_tools(self) -> List[BaseTool]:
        return [ChartColorSignalTool(), ChartStructureVisionTool()]

    def get_env_keys(self) -> List[ToolConfiguration]:
        return [
            ToolConfiguration(
                key="OMNICORE_WEBHOOK_URL",
                key_type=ToolConfigKeyType.STRING,
                is_required=False,
                is_secret=False,
            ),
            ToolConfiguration(
                key="OMNICORE_API_KEY",
                key_type=ToolConfigKeyType.STRING,
                is_required=False,
                is_secret=True,
            ),
            ToolConfiguration(
                key="OMNICORE_TIMEOUT_SECONDS",
                key_type=ToolConfigKeyType.INT,
                is_required=False,
                is_secret=False,
            ),
        ]
