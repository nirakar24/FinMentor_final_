import json
import os
import sys
from pathlib import Path

# Ensure repo root is on sys.path for package imports when running as a script
CURRENT_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from engine.engine import evaluate_payload


def main():
    sample = Path(__file__).resolve().parents[1] / "sample.json"
    with open(sample, "r", encoding="utf-8") as f:
        data = json.load(f)
    result = evaluate_payload(data)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
