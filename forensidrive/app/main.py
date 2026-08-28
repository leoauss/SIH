#!/usr/bin/env python3
"""ForensiDrive entry point. Run from the project root: python3 app/main.py"""

import os
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

os.environ.setdefault("FORENSIDRIVE_ROOT", str(APP_DIR.parent))


def main():
    import argparse
    import tkinter as tk

    from ui.app_window import AppWindow

    parser = argparse.ArgumentParser(description="ForensiDrive - Forensic Recovery & Data Sanitization Platform")
    parser.add_argument("--demo", "-d", action="store_true", help="Run with simulated storage drives for testing")
    args, _ = parser.parse_known_args()

    if args.demo:
        os.environ["FORENSIDRIVE_DEMO"] = "1"

    root = tk.Tk()
    AppWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
