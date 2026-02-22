"""Pytest configuration for MBTA tests."""

import sys
from pathlib import Path

# Add the main directory to sys.path so we can import modules
main_dir = Path(__file__).parent.parent / "main"
sys.path.insert(0, str(main_dir))
