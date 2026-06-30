"""Shared test configuration."""

import sys
from pathlib import Path

# Ensure the repository root is on the path so tests can import the agent package.
_REPO_ROOT = Path(__file__).parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
