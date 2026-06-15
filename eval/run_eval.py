"""
Run the eval over eval_cases.json and print a pass-rate table.

    python eval/run_eval.py
"""

from __future__ import annotations

import json
import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_service import ChatService  # noqa: E402

from google import genai  # noqa: E402
from google.genai import types  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
JUDGE_MODEL = "gemini-3.1-flash-lite"
_judge_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


def load_cases() -> list[dict]:
    with open(os.path.join(HERE, "eval_cases.json")) as f:
        return json.load(f)["cases"]


def judge(case: dict, answer: str) -> bool:
    """LLM-as-judge: returns True on PASS."""
    prompt = f"""You are an evaluation judge for a code explanation assistant called CodeLens.

Given:
- USER INPUT: {case['input']}
- EXPECTED BEHAVIOR: {case['expected']}
- ACTUAL ANSWER: {answer}

Decide if the actual answer satisfies the expected behavior.
Reply with exactly one word: PASS or FAIL.
"""
    response = _judge_client.models.generate_content(
        model=JUDGE_MODEL,
        contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
        config=types.GenerateContentConfig(temperature=0.0, max_output_tokens=10),
    )
    return "PASS" in (response.text or "").upper()


def run_variant(label: str, temperature: float = 0.4) -> dict:
    cases = load_cases()
    service = ChatService(temperature=temperature)
    passed = 0
    results = []
    for case in cases:
        service.reset()
        answer = service.send(case["input"])
        time.sleep(5)  # stay under 15 RPM free-tier limit
        ok = judge(case, answer)
        time.sleep(5)
        passed += int(ok)
        status = "PASS" if ok else "FAIL"
        results.append((case["id"], status, answer[:80].replace("\n", " ")))
        print(f"  [{status}] case {case['id']}: {answer[:60].replace(chr(10), ' ')}…")

    total = len(cases)
    rate = (passed / total * 100) if total else 0
    print(f"\n{label} (temp={temperature}): {passed}/{total} passed ({rate:.0f}%)\n")
    return {"label": label, "temperature": temperature, "passed": passed, "total": total, "rate": rate}


def write_results(variants: list[dict]) -> None:
    lines = [
        "# Eval Results\n",
        "## Pass-rate table\n",
        "| Variant | Temperature | Cases | Passed | Pass rate |",
        "|---------|-------------|-------|--------|-----------|",
    ]
    for v in variants:
        lines.append(
            f"| {v['label']} | {v['temperature']} | {v['total']} | {v['passed']} | {v['rate']:.0f}% |"
        )
    lines += [
        "",
        "## Rubric",
        "",
        "The judge (gemini-3.1-flash-lite) receives the user input, the expected behavior description,",
        "and the actual model answer. It replies PASS if the answer satisfies the expected behavior.",
        "",
        "## Verdict",
        "",
        "TODO: fill in after running — which variant is better and what the eval caught.",
    ]
    out_path = os.path.join(HERE, "eval_results.md")
    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Results written to {out_path}")


if __name__ == "__main__":
    print("=== Variant A: temperature=0.4 ===")
    a = run_variant("variant-A (temp=0.4)", temperature=0.4)

    print("=== Variant B: temperature=0.0 ===")
    b = run_variant("variant-B (temp=0.0)", temperature=0.0)

    write_results([a, b])
