"""Collapse the harness's per-chunk rollouts into one compact per-question file.

Run from auto-ontology-eval/runs/full_haiku after the benchmark:

    for L in chunk_*.log; do
      grep -oE "task_id=bird-[0-9]+ tokens: [0-9]+ in \\([0-9]+ cached\\), [0-9]+ out, [0-9]+ total over [0-9]+ LLM calls" "$L"
    done > tokens.txt
    python extract_summary.py   # writes summary.json

The raw rollouts (~200 MB) stay out of the repo; summary.json keeps, per question:
database, difficulty, question text, correctness in each arm, whether SQL was
produced, and token usage (treatment tokens come from the agent's own log line).
"""

import glob
import json
import re

tok = {}
for line in open("tokens.txt"):
    m = re.match(
        r"task_id=(\S+) tokens: (\d+) in \((\d+) cached\), (\d+) out, (\d+) total over (\d+) LLM calls",
        line,
    )
    if m:
        tok[m[1]] = dict(t_in=int(m[2]), t_out=int(m[4]), t_calls=int(m[6]))

out = []
for d in glob.glob("chunk_*/"):
    c = {r["task_id"]: r for r in map(json.loads, open(d + "control/bird.jsonl"))}
    t = {r["task_id"]: r for r in map(json.loads, open(d + "treatment/bird.jsonl"))}
    for i in c:
        cu = (c[i].get("response") or {}).get("usage") or {}
        out.append(
            dict(
                task_id=i,
                db_id=c[i]["db_id"],
                difficulty=c[i]["difficulty"],
                question=c[i]["question"][:200],
                c_ok=int(c[i]["reward"] > 0),
                t_ok=int(t[i]["reward"] > 0),
                c_fail=c[i].get("failure_kind"),
                t_fail=t[i].get("failure_kind"),
                c_sql=bool(c[i].get("extracted_sql")),
                t_sql=bool(t[i].get("extracted_sql")),
                c_in=cu.get("input_tokens"),
                c_out=cu.get("output_tokens"),
                **tok.get(i, {}),
            )
        )

json.dump(out, open("summary.json", "w"))
print(f"{len(out)} questions -> summary.json")
