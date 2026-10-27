import pandas as pd, polars as pl
import matplotlib.pyplot as plt
from benchmark import bench, make_ops, PAYMENT, CSV, DATES

pdf_full = pd.read_csv(CSV, parse_dates=DATES)
ldf_full = pl.read_csv(CSV, try_parse_dates=True)
pay_pd, pay_pl = pd.DataFrame(PAYMENT), pl.DataFrame(PAYMENT)

records = []
for frac in [0.1, 0.25, 0.5, 1.0]:
    pdf = pdf_full.sample(frac=frac, random_state=42)
    ldf = ldf_full.sample(fraction=frac, seed=42)
    p_ops, l_ops = make_ops(pdf, ldf, pay_pd, pay_pl)
    for op in ["filter", "groupby", "join", "sort"]:
        records.append((len(pdf), op, bench(p_ops[op], runs=3), bench(l_ops[op], runs=3)))

df = pd.DataFrame(records, columns=["rows", "operation", "pandas_s", "polars_s"])
df.to_csv("results_scalability.csv", index=False)

fig, axes = plt.subplots(1, 4, figsize=(18, 4))
for ax, (op, g) in zip(axes, df.groupby("operation")):
    ax.plot(g.rows, g.pandas_s, marker="o", label="Pandas")
    ax.plot(g.rows, g.polars_s, marker="o", label="Polars")
    ax.set_title(op); ax.set_xlabel("rows"); ax.set_ylabel("median time (s)")
    ax.legend()
plt.tight_layout()
plt.savefig("scalability.png", dpi=150)