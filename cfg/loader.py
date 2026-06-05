import tomllib
import os
import sys

def load_config(path: str = "config.toml") -> dict:
    if not os.path.exists(path):
        print(f"Error: Config file '{path}' not found.")
        sys.exit(1)
        
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        print(f"Error parsing '{path}': {e}")
        sys.exit(1)
