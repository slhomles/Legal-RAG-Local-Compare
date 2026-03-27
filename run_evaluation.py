"""
Script kiem thu so bo: do luong ty le ket luan co trich dan dung va lien quan.

Su dung:
  python run_evaluation.py
  python run_evaluation.py --json
"""
import sys
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from legal_rag.evaluation.evaluator import main

if __name__ == "__main__":
    main()
