"""app-etl: every CSV in a directory becomes a Parquet table and a JSON summary.

The package is the code a SageMaker processing job runs from the application image:
`python -m app_etl --input /opt/ml/processing/input --output /opt/ml/processing/output`.
`app_etl.pipeline` is the transformation and `app_etl.__main__` the command.
"""

__version__ = "0.1.0"
