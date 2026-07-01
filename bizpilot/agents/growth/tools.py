"""
Agent-specific tools for the Growth Strategist Agent.
"""

from typing import List, Dict, Any


def generate_gantt_milestones_tool(phases: list) -> Dict[str, Any]:
    """
    Placeholder tool to translate a list of phases into formatted Gantt/Milestone milestones.
    """
    return {"status": "Milestones compiled", "data": phases}


# List of tools to register with ADK Agent
growth_tools: List[Any] = [generate_gantt_milestones_tool]
