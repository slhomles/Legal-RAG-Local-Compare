"""
Tao du lieu mau (Hop_dong_A v1 & v2) de test pipeline.

Su dung:
    python scripts/create_sample_data.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from legal_rag.tools.create_sample_data import main

if __name__ == "__main__":
    main()
