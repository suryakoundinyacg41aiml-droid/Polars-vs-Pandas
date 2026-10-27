"""
plot_all.py - merge the clean per-library results and create the report figures.

Needs (in the same folder):
    results_pandas.csv, results_polars.csv                (from bench_one.py)
    results_scalability_pandas.csv, results_scalability_polars.csv  (from scalability_one.py)

Creates:
    results_benchmark_clean.csv, results_scalability_clean.csv
    benchmark_bar_clean.png, scalability_clean.png, memory_bar.png
"""
import pandas as pd
import matplotlib.pyplot as plt

# ---------------- Main benchmark ----------------
p = pd.read_csv("results_pandas.csv", index_col=0)
l = pd.read_csv("results_polars.csv", index_col=0)
bench = p.join(l)
bench["speedup_x"] = bench["pandas_s"] / bench["polars_s"]
bench.index.name = "operation"
bench.to_csv("results_benchmark_clean.csv")
print(bench.round(4))

ax = bench[["pandas_s", "polars_s"]].plot(kind="bar", figsize=(9, 4), logy=True)
ax.set_ylabel("median time (s, log scale)")
ax.set_title("Pandas vs Polars (10.9M rows)")
plt.tight_layout()
plt.savefig("benchmark_bar_clean.png", dpi=150)
plt.close()

# ---------------- Scalability ----------------
sp = pd.read_csv("results_scalability_pandas.csv")
sl = pd.read_csv("results_scalability_polars.csv")
sc = sp.merge(sl[["frac", "operation", "polars_s"]], on=["frac", "operation"])
sc["speedup_x"] = sc["pandas_s"] / sc["polars_s"]
sc.to_csv("results_scalability_clean.csv", index=False)
print(sc.round(4))

ops = list(sc["operation"].unique())
fig, axes = plt.subplots(1, len(ops), figsize=(4 * len(ops), 4))
for ax, op in zip(axes, ops):
    g = sc[sc["operation"] == op]
    ax.plot(g["rows"], g["pandas_s"], marker="o", label="Pandas")
    ax.plot(g["rows"], g["polars_s"], marker="o", label="Polars")
    ax.set_title(op)
    ax.set_xlabel("rows")
    ax.set_ylabel("median time (s)")
    ax.legend()
plt.tight_layout()
plt.savefig("scalability_clean.png", dpi=150)
plt.close()

# ---------------- Memory (values from mem.py) ----------------
mem = pd.DataFrame(
    {"in-memory data (MB)": [1669, 1581], "peak RSS (MB)": [2186, 2811]},
    index=["Pandas", "Polars"],
)
ax = mem.plot(kind="bar", figsize=(6, 4), rot=0)
ax.set_ylabel("MB")
ax.set_title("Memory: load CSV + groupby + sort")
plt.tight_layout()
plt.savefig("memory_bar.png", dpi=150)
plt.close()

print("Saved figures and clean CSVs.")