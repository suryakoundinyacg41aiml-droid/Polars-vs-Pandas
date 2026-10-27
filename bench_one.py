import sys, pandas as pd, polars as pl
from benchmark import bench, make_ops, PAYMENT, CSV, DATES

lib = sys.argv[1]
if lib == "pandas":
    df = pd.read_csv(CSV, parse_dates=DATES)
    ops, _ = make_ops(df, None, pd.DataFrame(PAYMENT), None)
else:
    df = pl.read_csv(CSV, try_parse_dates=True).rechunk()   
    _, ops = make_ops(None, df, None, pl.DataFrame(PAYMENT))

out = {name: bench(fn, runs=7) for name, fn in ops.items()}
pd.Series(out, name=f"{lib}_s").to_csv(f"results_{lib}.csv")
print(pd.Series(out))