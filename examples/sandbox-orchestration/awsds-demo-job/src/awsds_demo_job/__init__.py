"""awsds-demo-job: one CSV in, one JSON summary out.

Two entry points share one transformation:

    python -m awsds_demo_job      local directories: the processing job's mode
    python -m awsds_demo_job.s3   S3 prefixes through boto3: the MWAA worker's mode
"""

__version__ = "0.1.0"
