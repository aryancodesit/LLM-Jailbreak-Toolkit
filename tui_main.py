"""
TUI Entry Point — Phase 2
Usage: python tui_main.py
"""
import sys
import os

# Make sure project root is on path
sys.path.insert(0, os.path.dirname(__file__))

from tui.app import JailbreakApp

if __name__ == "__main__":
    JailbreakApp().run()
