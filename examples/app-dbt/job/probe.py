"""The processing job of the infrastructure repository's Stage 20 step 4.5: what a SageMaker
processing job without network isolation reaches from its project's network, on the house image.

It prints one line per reading: the interpreter and the SDK, the user, the proxy file the image
writes, the caller's identity, `SELECT 1` through the project's Athena workgroup, the product
database as Glue returns it, `ListLineageEvents` on the domain, and what the proxy answers a
request for a name on Sandbox's plane and for a name on no plane, the pair `sandbox/probes/` reads.
Each call is tried once with a 10-second connect timeout and prints its answer or one line REFUSED
with the error's type and text. The job exits 0 whatever a call answered: the reading is the log,
never the job's status.

    python probe.py --region us-west-2 --workgroup <workgroup> --database app_dbt --domain <domain>

"""

from __future__ import annotations

import argparse
import os
import platform
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Sequence
from typing import Any

# A name on Sandbox's proxy plane and a name on no plane, as sandbox/probes/ requests them.
ON_THE_PLANE = "https://pypi.org/"
ON_NO_PLANE = "http://example.com/"
# The file the house image writes: its proxy, the count of its NO_PROXY entries and their digest.
PROXY_FILE = "/opt/awsds-proxy.txt"
TIMEOUT_SECONDS = 10
QUERY_DEADLINE_SECONDS = 120


def show(name: str, *values: object) -> None:
    print(f"{name}:", *values, flush=True)


def call(name: str, thunk: Callable[[], Any]) -> Any:
    """The thunk's answer, or None after one line REFUSED: a client the SDK lacks fails here too."""
    try:
        return thunk()
    except Exception as error:
        show(name, "REFUSED", f"{type(error).__name__}:", str(error).replace("\n", " "))
        return None


def read(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read().strip().replace("\n", "; ")
    except OSError as error:
        return f"absent ({type(error).__name__})"


def query(
    name: str,
    athena: Any,
    workgroup: str,
    sql: str,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> None:
    started = call(name, lambda: athena.start_query_execution(QueryString=sql, WorkGroup=workgroup))
    if started is None:
        return
    execution = started["QueryExecutionId"]
    deadline = clock() + QUERY_DEADLINE_SECONDS
    while True:
        answer = call(name, lambda: athena.get_query_execution(QueryExecutionId=execution))
        if answer is None:
            return
        status = answer["QueryExecution"]["Status"]
        if status["State"] in ("SUCCEEDED", "FAILED", "CANCELLED") or clock() > deadline:
            break
        sleep(1)
    output = answer["QueryExecution"].get("ResultConfiguration", {}).get("OutputLocation")
    show(name, status["State"], status.get("StateChangeReason", "-"), "output", output)
    if status["State"] == "SUCCEEDED":
        result = call(name, lambda: athena.get_query_results(QueryExecutionId=execution))
        if result is not None:
            rows = result["ResultSet"]["Rows"]
            show(name, "rows", [[cell.get("VarCharValue") for cell in row["Data"]] for row in rows])


def fetch(name: str, url: str, opener: Callable[..., Any]) -> None:
    """The proxy's answer to one request, routed by the image's variables as any client's."""
    try:
        with opener(url, timeout=TIMEOUT_SECONDS) as response:
            show(name, url, "HTTP", response.status)
    except urllib.error.HTTPError as error:
        show(name, url, "HTTP", error.code, error.reason)
    except Exception as error:
        show(name, url, "REFUSED", f"{type(error).__name__}:", str(error).replace("\n", " "))


def boto3_clients(region: str) -> Callable[[str], Any]:
    import boto3
    import botocore
    from botocore.config import Config

    show("sdk", "boto3", boto3.__version__, "botocore", botocore.__version__)
    config = Config(
        region_name=region,
        connect_timeout=TIMEOUT_SECONDS,
        read_timeout=60,
        retries={"total_max_attempts": 1},
    )
    return lambda service: boto3.client(service, config=config)


def main(
    argv: Sequence[str] | None = None,
    clients: Callable[[str], Any] | None = None,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> int:
    parser = argparse.ArgumentParser(description="Stage 20 step 4.5's processing job")
    parser.add_argument("--region", required=True)
    parser.add_argument("--workgroup", required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--domain", required=True)
    args = parser.parse_args(argv)

    show("python", sys.executable, platform.python_version(), platform.platform())
    show("user", os.getuid(), os.getgid(), os.environ.get("HOME", "-"))
    show("proxy", os.environ.get("HTTPS_PROXY", "absent"), "file", read(PROXY_FILE))
    if clients is None:
        clients = boto3_clients(args.region)

    caller = call("caller", lambda: clients("sts").get_caller_identity())
    if caller is not None:
        show("caller", caller["Arn"])
    athena = call("athena", lambda: clients("athena"))
    if athena is not None:
        query("select 1", athena, args.workgroup, "SELECT 1")
    found = call("database", lambda: clients("glue").get_database(Name=args.database))
    if found is not None:
        entry = found["Database"]
        show("database", entry["Name"], entry.get("LocationUri"))
    events = call(
        "lineage",
        lambda: clients("datazone").list_lineage_events(
            domainIdentifier=args.domain, maxResults=10
        ),
    )
    if events is not None:
        items = events.get("items", [])
        show("lineage", len(items), "events", [item.get("processingStatus") for item in items])
    fetch("on the plane", ON_THE_PLANE, opener)
    fetch("on no plane", ON_NO_PLANE, opener)
    return 0


if __name__ == "__main__":
    sys.exit(main())
