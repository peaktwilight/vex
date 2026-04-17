from __future__ import annotations

import argparse
import json
from pathlib import Path

from .predictor import predict

DATASET = Path(__file__).resolve().parents[2] / "evals" / "datasets" / "cases.jsonl"


def _run_case(case: dict[str, object]) -> dict[str, object]:
    text = str(case.get("input", ""))
    expected_label = str(case.get("expect_label", "")).lower()
    result = predict(text)
    label = str(result["label"]).lower()
    passed = (not expected_label) or expected_label == label
    return {
        "input": text,
        "label": label,
        "expected": expected_label,
        "passed": passed,
    }


def _run_all(inputs: list[str]) -> int:
    cases = [
        json.loads(line)
        for line in DATASET.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if inputs:
        cases = [c for c in cases if str(c.get("input", "")) in inputs]
    if not cases:
        print("no cases")
        return 0
    results = [_run_case(c) for c in cases]
    passed = sum(1 for r in results if r["passed"])
    for r in results:
        marker = "PASS" if r["passed"] else "FAIL"
        print(
            f"[{marker}] {r['input']!r} -> label={r['label']!r} "
            f"(expected {r['expected']!r})"
        )
    print(f"eval: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", action="append", default=[])
    args = parser.parse_args()
    raise SystemExit(_run_all(args.input))


if __name__ == "__main__":
    main()
