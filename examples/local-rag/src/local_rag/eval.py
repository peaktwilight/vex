from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from . import retriever
from .agent import build_agent

DATASET = Path(__file__).resolve().parents[2] / "evals" / "datasets" / "cases.jsonl"


async def _run_case(agent, case: dict[str, object]) -> dict[str, object]:
    prompt = str(case.get("input", ""))
    expected_fact = str(case.get("expect_contains", "")).lower()
    expected_doc = str(case.get("expect_doc", "")).lower()
    top_docs = [h.doc.lower() for h in retriever.search(prompt, k=3)]
    output = str((await agent.run(prompt)).output)
    passed = True
    if expected_fact:
        passed = passed and expected_fact in output.lower()
    if expected_doc:
        passed = passed and expected_doc in top_docs
    return {"input": prompt, "output": output, "retrieved": top_docs, "passed": passed}


async def _run_all(inputs: list[str]) -> int:
    agent = build_agent()
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
    results = [await _run_case(agent, c) for c in cases]
    passed = sum(1 for r in results if r["passed"])
    for r in results:
        marker = "PASS" if r["passed"] else "FAIL"
        print(f"[{marker}] {r['input']!r} retrieved={r['retrieved']} -> {r['output']!r}")
    print(f"eval: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", action="append", default=[])
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_run_all(args.input)))


if __name__ == "__main__":
    main()
