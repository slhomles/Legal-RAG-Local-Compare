import io
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT / "src"))

from legal_rag.evaluation.citation_evaluator import CitationEvaluator


def main():
    report_path = PROJECT_ROOT / "compare_report_dump.json"
    output_path = PROJECT_ROOT / "citation_evaluation_dump.json"

    with open(report_path, "r", encoding="utf-8") as f:
        report_data = json.load(f)

    evaluator = CitationEvaluator()
    evaluation_result = evaluator.evaluate_report(report_data)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(evaluation_result, f, ensure_ascii=False, indent=2)

    print(json.dumps(evaluation_result, ensure_ascii=False, indent=2))
    print(f"\nĐã lưu kết quả evaluation vào file: {output_path}")


if __name__ == "__main__":
    main()