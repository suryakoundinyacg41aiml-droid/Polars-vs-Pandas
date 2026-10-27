import time, gc, statistics
import pandas as pd
import polars as pl

CSV = "data/yellow_tripdata_2016-01.csv"
DATES = ["tpep_pickup_datetime", "tpep_dropoff_datetime"]

PAYMENT = {
    "payment_type": [1, 2, 3, 4, 5, 6],
    "payment_name": ["Credit card", "Cash", "No charge", "Dispute", "Unknown", "Voided trip"],
}

def bench(fn, runs=5):
    times = []
    for _ in range(runs):
        gc.collect()
        t = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t)
    return statistics.median(times)

def make_ops(pdf, ldf, pay_pd, pay_pl):
    pandas_ops = {
        "filter": lambda: pdf[(pdf.trip_distance > 5) & (pdf.fare_amount > 20)],
        "select": lambda: pdf[["VendorID", "passenger_count", "trip_distance", "fare_amount", "tip_amount"]],
        "groupby": lambda: pdf.groupby("payment_type").agg(
            avg_fare=("fare_amount", "mean"),
            avg_tip=("tip_amount", "mean"),
            total_dist=("trip_distance", "sum"),
            trips=("fare_amount", "count")),
        "groupby_hour": lambda: pdf.groupby(pdf.tpep_pickup_datetime.dt.hour)["total_amount"].mean(),
        "join": lambda: pdf.merge(pay_pd, on="payment_type", how="left"),
        "sort": lambda: pdf.sort_values("total_amount", ascending=False),
        "transform": lambda: pdf.assign(
            duration_min=(pdf.tpep_dropoff_datetime - pdf.tpep_pickup_datetime).dt.total_seconds() / 60,
            tip_pct=pdf.tip_amount / pdf.fare_amount.where(pdf.fare_amount > 0)),
    }
    polars_ops = {
        "filter": lambda: ldf.filter((pl.col("trip_distance") > 5) & (pl.col("fare_amount") > 20)),
        "select": lambda: ldf.select(["VendorID", "passenger_count", "trip_distance", "fare_amount", "tip_amount"]),
        "groupby": lambda: ldf.group_by("payment_type").agg(
            pl.col("fare_amount").mean().alias("avg_fare"),
            pl.col("tip_amount").mean().alias("avg_tip"),
            pl.col("trip_distance").sum().alias("total_dist"),
            pl.col("fare_amount").count().alias("trips")),
        "groupby_hour": lambda: ldf.group_by(pl.col("tpep_pickup_datetime").dt.hour()).agg(
            pl.col("total_amount").mean()),
        "join": lambda: ldf.join(pay_pl, on="payment_type", how="left"),
        "sort": lambda: ldf.sort("total_amount", descending=True),
        "transform": lambda: ldf.with_columns(
            ((pl.col("tpep_dropoff_datetime") - pl.col("tpep_pickup_datetime")).dt.total_seconds() / 60)
            .alias("duration_min"),
            (pl.col("tip_amount") / pl.when(pl.col("fare_amount") > 0).then(pl.col("fare_amount")))
            .alias("tip_pct")),
    }
    return pandas_ops, polars_ops

if __name__ == "__main__":
    # ---- Load benchmark (fewer runs: each takes a while) ----
    load_pd = bench(lambda: pd.read_csv(CSV, parse_dates=DATES), runs=3)
    load_pl = bench(lambda: pl.read_csv(CSV, try_parse_dates=True), runs=3)

    pdf = pd.read_csv(CSV, parse_dates=DATES)
    ldf = pl.read_csv(CSV, try_parse_dates=True)
    print("Rows:", len(pdf), "| Columns:", pdf.shape[1], "| polars rows:", ldf.height)
    print(pdf.dtypes)   # confirm both dtypes line up

    pay_pd = pd.DataFrame(PAYMENT)
    pay_pl = pl.DataFrame(PAYMENT)

    pandas_ops, polars_ops = make_ops(pdf, ldf, pay_pd, pay_pl)

    rows = [("load_csv", load_pd, load_pl)]
    for op in pandas_ops:
        rows.append((op, bench(pandas_ops[op]), bench(polars_ops[op])))

    out = pd.DataFrame(rows, columns=["operation", "pandas_s", "polars_s"])
    out["speedup_x"] = out.pandas_s / out.polars_s
    print(out.round(4).to_string(index=False))
    out.to_csv("results_benchmark.csv", index=False)

    # ---- Equivalence checks ----
    a = pandas_ops["groupby"]().sort_index().reset_index()
    b = polars_ops["groupby"]().sort("payment_type").to_pandas()
    assert a.payment_type.tolist() == b.payment_type.tolist()
    for c in ["avg_fare", "avg_tip", "total_dist", "trips"]:
        assert abs(a[c] - b[c]).max() < 1e-6, c
    assert len(pandas_ops["filter"]()) == polars_ops["filter"]().height
    assert len(pandas_ops["join"]()) == polars_ops["join"]().height
    print("Equivalence checks passed.")