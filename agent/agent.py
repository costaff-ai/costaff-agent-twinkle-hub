import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from google.adk.agents import LlmAgent

from instruction import build_instruction
from mcp_toolsets import load_all_mcp_toolsets
from models import selected_model
from skills import load_all_skills
from sub_agents import load_all_sub_agents
from progress import (
    before_model_callback,
    before_tool_callback,
    after_tool_callback,
)

tools = list(load_all_mcp_toolsets())
tools.append(load_all_skills())

sub_agents = load_all_sub_agents()

instruction = build_instruction()

twinkle_hub_agent = LlmAgent(
    name="twinkle_hub_agent",
    model=selected_model,
    description="Taiwan open data curator: searches, queries, and materializes datasets from Twinkle Hub across 19 domains.",
    instruction=instruction,
    # Code-driven live panel (same canonical progress.py as every agent).
    before_model_callback=before_model_callback,
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback,
    tools=tools,
    sub_agents=sub_agents,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)
