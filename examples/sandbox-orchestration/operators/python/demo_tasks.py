"""The PythonOperator task of `demo-python-operator` (Stage 6i step 4).

The portal names it as module `demo_tasks`, function `run`, with `bucket`, `inbox` and
`outbox` as its op kwargs. Before handing the work to the project's worker mode it prints
what the worker runs it with: the interpreter, the caller's ARN, and where each vendored
package was imported from, which is how a bundled copy is told from a pre-installed one.
"""

from __future__ import annotations

import importlib
import sys

# petl is absent from the worker's pre-installed set; PyYAML is in it, unpinned. The
# archive vendors both (requirements.txt), so __file__ says which copy each import found.
VENDORED = ("petl", "yaml")


def run(bucket: str, inbox: str, outbox: str, **_context) -> int:
    import boto3

    print(f"python {sys.version.split()[0]} at {sys.executable}")
    print(f"caller {boto3.client('sts').get_caller_identity()['Arn']}")
    for name in VENDORED:
        try:
            module = importlib.import_module(name)
        except ImportError as exc:
            print(f"import {name}: FAILED - {exc}")
            continue
        version = getattr(module, "__version__", "-")
        print(f"import {name}: {version} from {getattr(module, '__file__', '-')}")

    from awsds_demo_job import s3

    processed = s3.run(bucket, inbox, outbox)
    if not processed:
        raise RuntimeError(f"nothing under s3://{bucket}/{inbox} - the sensor saw a file")
    return processed
