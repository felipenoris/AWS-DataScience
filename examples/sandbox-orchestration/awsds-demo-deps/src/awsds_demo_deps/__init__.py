"""awsds-demo-deps: one CSV in, a Parquet table and a JSON summary out.

    python -m awsds_demo_deps --input DIR --output DIR

The same summary awsds-demo-job writes, read with petl and encoded with msgspec, and the rows
as a Parquet table written with pyarrow.
"""

__version__ = "0.1.0"
