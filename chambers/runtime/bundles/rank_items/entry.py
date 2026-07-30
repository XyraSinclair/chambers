"""A deterministic ranking as an R2 workload (RUNNER-SPEC §6) — the
metered sort's comparator tier: items in, total order out. The tie-break
is explicit (merit desc, then name asc); nothing depends on input order,
set iteration, clock, or environment.
"""
import json

items = json.load(open("inputs/items.json", encoding="utf-8"))
ranked = sorted(items, key=lambda it: (-it["merit"], it["name"]))
with open("output", "w", encoding="ascii") as fh:
    fh.write(json.dumps([it["name"] for it in ranked],
                        sort_keys=True, separators=(",", ":")))
