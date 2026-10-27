import sys, time, resource

lib = sys.argv[1]
CSV = "data/yellow_tripdata_2016-01.csv"

if lib == "pandas":
    import pandas as pd
    df = pd.read_csv(CSV, parse_dates=["tpep_pickup_datetime", "tpep_dropoff_datetime"])
    df.groupby("payment_type")["fare_amount"].mean()
    df.sort_values("total_amount")
    data_mb = df.memory_usage(deep=True).sum() / 1e6
else:
    import polars as pl
    df = pl.read_csv(CSV, try_parse_dates=True)
    df.group_by("payment_type").agg(pl.col("fare_amount").mean())
    df.sort("total_amount")
    data_mb = df.estimated_size() / 1e6

peak_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6   # bytes on macOS
print(f"{lib}: in-memory data = {data_mb:.0f} MB | peak RSS = {peak_mb:.0f} MB")