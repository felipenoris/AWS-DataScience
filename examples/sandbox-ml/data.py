"""Stage 17 step 2.1: the recipe's CSV fetched, prepared, split and written to the project.

Fetches the Telco customer churn CSV from GitHub through the space's proxy (the name is on the
compute plane's allow-list), prepares and splits it with `prepare.py`, and writes four objects
under the project's shared/ml-demo/data/:

    raw/telco.csv          the CSV as fetched: the pipeline's processing step splits it again
    train.csv              70%, XGBoost's layout (label first, no header)
    validation.csv         15%, the same layout: the training channel and the transform's input
    test.csv               15%, the same layout

It prints the row counts and the keys, never a row. The proxy's access log line for the fetch is
the stage's reading (verification xxvi).

    /opt/awsds/venv/bin/python data.py
"""

from __future__ import annotations

import io
import sys
import urllib.request

import pandas as pd
from common import client, demo_prefix, load_values
from prepare import prepare, split, to_csv

SOURCE = (
    "https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/"
    "Telco-Customer-Churn.csv"
)


def main() -> int:
    values = load_values()
    s3 = client(values, "s3")
    bucket, prefix = values["PROJECTS_BUCKET"], f"{demo_prefix(values)}/data"

    # urllib reads HTTPS_PROXY, which the house image sets, and the OS trust store, which holds
    # the proxy's root.
    with urllib.request.urlopen(SOURCE, timeout=60) as response:
        raw_bytes = response.read()
    raw = pd.read_csv(io.BytesIO(raw_bytes))
    print(f"fetched {len(raw)} rows, {len(raw_bytes)} bytes, from {SOURCE}")

    s3.put_object(Bucket=bucket, Key=f"{prefix}/raw/telco.csv", Body=raw_bytes)
    print(f"raw: s3://{bucket}/{prefix}/raw/telco.csv")

    table = prepare(raw)
    print(f"prepared: {len(table)} rows, {len(raw) - len(table)} dropped for a blank TotalCharges")
    for name, rows in split(table).items():
        key = f"{prefix}/{name}.csv"
        s3.put_object(Bucket=bucket, Key=key, Body=to_csv(rows).encode("utf-8"))
        print(f"{name}: {len(rows)} rows -> s3://{bucket}/{key}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
