import os
import sys


# Make the src/ folder importable during tests.
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
SRC_PATH = os.path.join(PROJECT_ROOT, "src")

# Insert src/ at the front so imports like app.utils... work.
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)