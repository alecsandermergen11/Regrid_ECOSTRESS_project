import os
import sys

# Ensure src/ is on sys.path so `regrid_project` package can be imported
ROOT = os.path.dirname(__file__)
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import src.regrid_project.plot_results as plot_results

if __name__ == "__main__":
    plot_results.main()
