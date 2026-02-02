"""Pytest configuration for agent tests.

Sets up the Python path to allow imports from src/.
"""

import sys
from pathlib import Path

# Add the agent directory (parent of src) to Python path
# This allows imports like "from src.config import ..." to work
agent_path = Path(__file__).parent.parent
if str(agent_path) not in sys.path:
    sys.path.insert(0, str(agent_path))

# Also add src directory for backwards compatibility with existing tests
src_path = agent_path / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
