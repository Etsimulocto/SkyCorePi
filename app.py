#!/usr/bin/env python3
"""SkyCorePi main entry point: BRO development console."""
if __name__ == "__main__":
    import runpy
    import sys
    from pathlib import Path
    directory=Path(__file__).resolve().parent/"apps"/"BRO"
    sys.path.insert(0,str(directory))
    runpy.run_path(str(directory/"bloomface.py"),run_name="__main__")
