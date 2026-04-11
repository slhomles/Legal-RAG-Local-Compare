"""
Sinh bao cao Word - Muc III.

Su dung:
    python scripts/generate_word_report.py
    python scripts/generate_word_report.py --doc-id Hop_dong_A --old v1 --new v2
    python scripts/generate_word_report.py --from-json output/report_data.json
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from legal_rag.generation.word_report import main

if __name__ == "__main__":
    main()
