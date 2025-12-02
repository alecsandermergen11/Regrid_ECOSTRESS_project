import os
import sys

# Ensure src/ is on sys.path so `regrid_project` package can be imported
ROOT = os.path.dirname(__file__)
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

# Import the root script and run (package import)
import src.regrid_project.main as main

if __name__ == "__main__":
    # main.process_single_file acts as the orchestrator when called with no args
    main.process_single_file()
