# tests/conftest.py
import sys
import os

# Get the absolute path to the directory containing conftest.py (i.e., the 'tests' directory)
tests_dir = os.path.dirname(os.path.abspath(__file__))

# Get the absolute path to the project root directory (one level up from 'tests')
project_root = os.path.abspath(os.path.join(tests_dir, '..'))

# Insert the project root directory at the beginning of sys.path
# This makes modules directly in the project root (like video_player.py) importable.
sys.path.insert(0, project_root)

print(f"DEBUG: Added {project_root} to sys.path for tests.") # Optional: for debugging
