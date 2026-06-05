import os
import yaml

STRATEGIES_DIR = "strategies"

def list_strategies() -> list[str]:
    if not os.path.exists(STRATEGIES_DIR):
        return []
    strategies = []
    for f in os.listdir(STRATEGIES_DIR):
        if f.endswith(".yaml"):
            strategies.append(f[:-5])
    return sorted(strategies)

def load_strategy(name: str) -> dict:
    path = os.path.join(STRATEGIES_DIR, f"{name}.yaml")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Strategy file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if "name" not in data:
        data["name"] = name.capitalize()
    return data
