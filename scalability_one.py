"""
scalability_one.py - scalability test for ONE library per process.

Usage:
    python scalability_one.py pandas
    python scalability_one.py polars

Requires benchmark.py in the same folder (for bench, make_ops, PAYMENT, CSV, DATES).
Outputs results_scalability_<lib>.csv
"""
import sys
import gc

import pandas as pd
import polars as pl

from benchmark import bench, make_ops, PAYMENT, CSV, DATES

FRACS = [0.1, 0.25, 0.5, 1.0]
OPS = ["filter", "groupby", "join", "sort", "transform"]
RUNS = 5

lib = sys.argv[1] if len(sys.argv) > 1 else None
if lib not in ("pandas", "polars"):
    print("Usage: python scalability_one.py [pandas|polars]")
    sys.exit(1)

if lib == "pandas":
    full = pd.read_csv(CSV, parse_dates=DATES)
    pay = pd.DataFrame(PAYMENT)
else:
    full = pl.read_csv(CSV, try_parse_dates=True).rechunk()
    pay = pl.DataFrame(PAYMENT)

records = []
for frac in FRACS:
    if frac == 1.0:
        sub = full  # no extra copy at full size
    elif lib == "pandas":
        sub = full.sample(frac=frac, random_state=42)
    else:
        sub = full.sample(fraction=frac, seed=42).rechunk()

    n_rows = len(sub) if lib == "pandas" else sub.height

    if lib == "pandas":
        ops, _ = make_ops(sub, None, pay, None)
    else:
        _, ops = make_ops(None, sub, None, pay)

    for op in OPS:
        t = bench(ops[op], runs=RUNS)
        records.append((frac, n_rows, op, t))
        print(f"frac={frac:<5} rows={n_rows:<10} {op:<10} {t:.4f} s")

    if frac != 1.0:
        del sub, ops
        gc.collect()

out = pd.DataFrame(records, columns=["frac", "rows", "operation", f"{lib}_s"])
out.to_csv(f"results_scalability_{lib}.csv", index=False)
print(f"\nSaved results_scalability_{lib}.csv")