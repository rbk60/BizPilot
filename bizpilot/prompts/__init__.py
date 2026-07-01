"""
Global prompts package.
Provides utilities to load and parse system instructions and templates.
"""

import os


def load_prompt_template(agent_name: str) -> str:
    """
    Helper utility to load prompts from agent sub-directories.
    
    Args:
        agent_name: Name of the agent subdirectory (e.g. 'core', 'strategy')
        
    Returns:
        The content of prompt.md as a string.
    """
    # Simple prompt loading utility
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompt_path = os.path.join(base_dir, "agents", agent_name, "prompt.md")
    
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    return f"Default persona instruction for agent: {agent_name}"
