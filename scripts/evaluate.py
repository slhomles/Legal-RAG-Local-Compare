"""
Kiem thu do luong chat luong he thong: citation accuracy, change detection, guardrail.

Su dung:
    python scripts/evaluate.py
    python scripts/evaluate.py --json
"""
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from legal_rag.evaluation.evaluator import main

if __name__ == "__main__":
    main()
