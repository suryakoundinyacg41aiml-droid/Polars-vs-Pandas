import pandas as pd, matplotlib.pyplot as plt
df = pd.read_csv("results_benchmark.csv").set_index("operation")
df[["pandas_s", "polars_s"]].plot(kind="bar", figsize=(9, 4), logy=True)
plt.ylabel("median time (s, log scale)")
plt.tight_layout(); plt.savefig("benchmark_bar.png", dpi=150)