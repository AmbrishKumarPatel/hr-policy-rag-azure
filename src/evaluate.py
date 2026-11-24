import csv
import json
import os
from datetime import datetime

import config
from azure_clients import get_openai_client
from search import search
from rag import ask

TOP_K = 5   # rag.py bhi itne hi chunks leta hai
EVAL_DIR = os.path.join(os.path.dirname(__file__), "..", "eval")

judge_client = get_openai_client()

JUDGE_PROMPT = """You are a strict evaluator.
Check if every claim in the ANSWER is supported by the CONTEXT.
Score from 1 to 5:
5 = every claim is supported
3 = some claims are not supported
1 = most claims are not supported or made up
Reply only in JSON: {"score": <1-5>, "reason": "<one short sentence>"}"""


def groundedness(context, answer):
    """LLM-as-a-judge: jawab ki har baat context me hai ya nahi (1-5)."""
    response = judge_client.chat.completions.create(
        model=config.AZURE_OPENAI_CHAT_DEPLOYMENT,
        messages=[
            {"role": "system", "content": JUDGE_PROMPT},
            {"role": "user", "content": f"CONTEXT:\n{context}\n\nANSWER:\n{answer}"},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    result = json.loads(response.choices[0].message.content)
    return int(result["score"]), result["reason"]


def find_rank(hits, source, page):
    """Sahi page search result me kis number pe aaya (1 se shuru). Nahi mila to 0."""
    for rank, h in enumerate(hits, start=1):
        if h["source"] == source and h["page"] == page:
            return rank
    return 0


def evaluate_one(case):
    hits = search(case["question"], case["user_groups"], top=TOP_K)
    result = ask(case["question"], case["user_groups"])
    answer = result["answer"]
    row = {"id": case["id"], "type": case["type"], "question": case["question"],
           "answer": answer.replace("\n", " ")[:300], "blocked": result["blocked"]}

    # ---- Check 1: Retrieval (sirf un sawalon pe jinka sahi page pata hai) ----
    if case["expected_source"]:
        rank = find_rank(hits, case["expected_source"], case["expected_page"])
        row["hit"] = 1 if rank else 0
        row["reciprocal_rank"] = round(1 / rank, 3) if rank else 0
    else:
        row["hit"] = row["reciprocal_rank"] = ""

    # ---- Check 2a: Correctness (zaruri shabd jawab me hai?) ----
    text = answer.lower().replace("’", "'")
    row["correct"] = 1 if all(w.lower() in text for w in case["must_contain"]) else 0

    # ---- Check 2b: Security (mana kiye documents search me aaye?) ----
    if case.get("forbidden_sources"):
        leaked = [h["source"] for h in hits if h["source"] in case["forbidden_sources"]]
        row["security_ok"] = 0 if leaked else 1
    else:
        row["security_ok"] = ""

    # ---- Check 2c: Groundedness (sirf asli jawab pe, "I don't know" ya block pe nahi) ----
    if not result["blocked"] and "don't know" not in text:
        context = "\n\n".join(f"[{h['source']}, page {h['page']}]\n{h['content']}" for h in hits)
        row["groundedness"], row["judge_reason"] = groundedness(context, answer)
    else:
        row["groundedness"], row["judge_reason"] = "", ""

    return row


def average(rows, key):
    values = [r[key] for r in rows if r[key] != ""]
    return round(sum(values) / len(values), 3) if values else None


if __name__ == "__main__":
    with open(os.path.join(EVAL_DIR, "testset.json"), encoding="utf-8") as f:
        testset = json.load(f)

    rows = []
    for case in testset:
        row = evaluate_one(case)
        rows.append(row)
        print(f"#{row['id']:>2} {row['type']:<12} hit={row['hit']!s:<2} correct={row['correct']} "
              f"secure={row['security_ok']!s:<2} grounded={row['groundedness']!s:<2} | {case['question'][:45]}")

    print("\n========== SUMMARY ==========")
    print(f"Recall@{TOP_K}       : {average(rows, 'hit')}")
    print(f"MRR             : {average(rows, 'reciprocal_rank')}")
    print(f"Correctness     : {average(rows, 'correct')}")
    print(f"Security pass   : {average(rows, 'security_ok')}")
    print(f"Groundedness    : {average(rows, 'groundedness')} (out of 5)")

    # Har run ka result file me, taaki baad me compare kar sake
    out_dir = os.path.join(EVAL_DIR, "results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"run_{datetime.now():%Y%m%d_%H%M}.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print("\nDetail saved:", out_path)