"""Plain Python function tools — always available to the LLM
(unlike SkillToolset, which loads skills on demand).

To add a new tool:
    1. Create <tool_name>.py in this folder, defining a function with a
       clear docstring (the docstring tells the agent when to call this tool).
    2. Import the function here and add it to __all__.
    3. In agent.py, import from tools and include it in Agent(tools=[...]).

Currently empty — placeholder for future plain-Python function tools.
"""

__all__: list = []
