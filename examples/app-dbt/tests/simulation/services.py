"""The services app-dbt's simulation runs the task against, in one process, with no AWS call.

    MOTO_ACCOUNT_ID=000000000000 python services.py

Run by simulate.py in an environment holding moto[server] 5.2.5. It prints one line of JSON naming
its two ports, then serves until its standard input closes:

- **The recorder**, moto's Athena, Glue, S3 and STS behind a WSGI layer, the endpoint every client
  of a case reaches through AWS_ENDPOINT_URL. The layer writes each call's service and operation to
  the trail. moto answers an Athena statement without running it, so the layer gives a create, a
  rename and a drop their effect in Glue, refuses a statement that reads a table Glue does not hold,
  seeds the rows a statement's reader expects, and answers GetQueryExecution with the statement's
  type, which moto reads from the first word and dbt's query comment hides. A service moto does not
  serve, DataZone, is answered 501.
- **The listener**, the domain's endpoint as the lineage transport's endpointOverride reaches it:
  PostLineageEvent answered 200 with an id, or 403 AccessDeniedException, each body recorded with
  whether the request carried a SigV4 signature for datazone.

The control paths under /_simulation/ on the recorder reset the account (`reset`, with the Glue
database, the workgroup and the source table each optional), clear the trail and the events
(`clear`), set the listener's answer and the outcome of dbt's test (`mode`), and read the trail and
the events.
"""

from __future__ import annotations

import io
import json
import logging
import os
import re
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs

from moto.athena.models import QueryResults, athena_backends
from moto.glue.models import glue_backends
from moto.moto_server.werkzeug_app import (
    DomainDispatcherApplication,
    MotoRequestHandler,
    create_backend_app,
)
from werkzeug.serving import make_server

ACCOUNT = os.environ["MOTO_ACCOUNT_ID"]
REGION = "us-west-2"

# The leading comment dbt writes before each statement, and the line comments a model may carry.
QUERY_COMMENT = re.compile(r"^\s*(?:/\*.*?\*/\s*)+", re.S)
LINE_COMMENT = re.compile(r"--[^\n]*")
CTAS = re.compile(
    r"^create\s+table\s+(?P<name>[^\s(]+)\s+with\s*\((?P<properties>.*?)\)\s*as\s+(?P<select>.*)$",
    re.I | re.S,
)
RENAME = re.compile(r"^alter\s+table\s+(?P<source>\S+)\s+rename\s+to\s+(?P<target>\S+?);?$", re.I)
DROP = re.compile(r"^drop\s+table\s+(?P<exists>if\s+exists\s+)?(?P<name>\S+?);?$", re.I)
PROPERTY = re.compile(r"(\w+)\s*=\s*'([^']*)'")
REFERENCE = re.compile(r"\b(?:from|join)\s+((?:[\"`]?\w+[\"`]?\.){1,2}[\"`]?\w+[\"`]?)", re.I)
CONSTANT = re.compile(r"^select\s+'(?P<value>[^']*)'\s*;?$", re.I | re.S)
SELECT_ONE = re.compile(r"^select\s+1(?:\s+as\s+(?P<alias>\w+))?\s*;?$", re.I)
COUNT = re.compile(r"^select\s+count\(\*\)\s+from\s", re.I)
ALIAS = re.compile(r"\s+as\s+[\"`]?(?P<alias>\w+)[\"`]?\s*$", re.I | re.S)
DATAZONE_PATHS = (
    ("GET", re.compile(r"^/v2/domains/[^/]+/lineage/events$"), "ListLineageEvents"),
    ("POST", re.compile(r"^/v2/domains/[^/]+/lineage/events$"), "PostLineageEvent"),
)
TABLE_INPUT_KEYS = ("Description", "Owner", "StorageDescriptor", "PartitionKeys", "TableType")


class Failure(Exception):
    """A statement Athena would end FAILED, with the reason it gives."""


def column(name: str, kind: str) -> dict[str, Any]:
    return {
        "CatalogName": "hive",
        "SchemaName": "",
        "TableName": "",
        "Name": name,
        "Label": name,
        "Type": kind,
        "Precision": 19 if kind == "bigint" else 0,
        "Scale": 0,
        "Nullable": "UNKNOWN",
        "CaseSensitive": kind == "varchar",
    }


def rows(*values: tuple[str, ...]) -> list[dict[str, Any]]:
    return [{"Data": [{"VarCharValue": value} for value in row]} for row in values]


def name_of(text: str) -> tuple[str, str]:
    """The database and the table of a name written as `a.b.c` or `a.b`, quoted or not."""
    parts = [part.strip('"`') for part in text.split(".")]
    return parts[-2].lower(), parts[-1].lower()


def top_level_split(text: str) -> list[str]:
    """`text` split at the commas outside parentheses."""
    items, depth, start = [], 0, 0
    for index, character in enumerate(text):
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
        elif character == "," and depth == 0:
            items.append(text[start:index])
            start = index + 1
    items.append(text[start:])
    return [item.strip() for item in items if item.strip()]


class Simulation:
    """The account's state the recorder and the listener share, and what each case reads back."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.trail: list[dict[str, Any]] = []
        self.events: list[dict[str, Any]] = []
        self.statements: dict[str, dict[str, Any]] = {}
        self.mode = {"listener": "answer", "test": "pass"}
        self.setup: dict[str, Any] = {}

    @property
    def glue(self) -> Any:
        return glue_backends[ACCOUNT][REGION]

    @property
    def athena(self) -> Any:
        return athena_backends[ACCOUNT][REGION]

    def reset(self, setup: dict[str, Any]) -> None:
        """A fresh account: the Glue database, the workgroup and the source table, as asked."""
        self.glue.reset()
        self.athena.reset()
        self.clear()
        self.setup = setup
        database = setup["database"]
        if setup.get("with_database", True):
            self.glue.create_database(
                database,
                {
                    "Name": database,
                    "LocationUri": setup["location"],
                    "CreateTableDefaultPermissions": [],
                },
            )
        if setup.get("with_workgroup", True):
            configuration = {
                "ResultConfiguration": {"OutputLocation": setup["output"]},
                "EnforceWorkGroupConfiguration": True,
                "PublishCloudWatchMetricsEnabled": True,
                "EngineVersion": {
                    "SelectedEngineVersion": "Athena engine version 3",
                    "EffectiveEngineVersion": "Athena engine version 3",
                },
            }
            self.athena.create_work_group(
                name=setup["workgroup"], configuration=configuration, description="", tags=[]
            )
        if setup.get("with_database", True) and setup.get("with_source", True):
            columns = [{"Name": name, "Type": kind} for name, kind in setup["source_columns"]]
            location = f"{setup['location'].rstrip('/')}/{setup['source']}"
            self.create_table(database, setup["source"], location, columns)

    def clear(self) -> None:
        with self.lock:
            self.trail.clear()
            self.events.clear()
            self.statements.clear()

    def create_table(
        self, database: str, table: str, location: str, columns: list[dict[str, str]]
    ) -> None:
        location = location.rstrip("/")
        table_input = {
            "Name": table,
            "TableType": "EXTERNAL_TABLE",
            "Parameters": {
                "table_type": "ICEBERG",
                "metadata_location": f"{location}/metadata/00000-{uuid.uuid4()}.metadata.json",
            },
            "StorageDescriptor": {"Columns": columns, "Location": location},
        }
        try:
            self.glue.create_table(database, table, table_input)
        except Exception as error:
            raise Failure(
                f"ALREADY_EXISTS: Table '{database}.{table}' exists ({type(error).__name__})"
            ) from error

    def table(self, database: str, table: str) -> dict[str, Any] | None:
        try:
            return self.glue.get_table(database, table).as_dict()
        except Exception:
            return None

    def require_sources(self, sql: str) -> dict[str, Any] | None:
        """The last table a statement reads; a table Glue does not hold fails the statement."""
        found = None
        for reference in REFERENCE.findall(sql):
            database, table = name_of(reference)
            found = self.table(database, table)
            if found is None:
                raise Failure(
                    f"TABLE_NOT_FOUND: line 1:1: Table 'awsdatacatalog.{database}.{table}' "
                    "does not exist"
                )
        return found

    def select_columns(self, select: str, source: dict[str, Any] | None) -> list[dict[str, str]]:
        """The columns a CTAS's select list writes: a source column keeps its type, an expression
        is a double."""
        known = {}
        if source is not None:
            for entry in source.get("StorageDescriptor", {}).get("Columns", []):
                known[entry["Name"].lower()] = entry["Type"]
        body = re.sub(r"^\s*select\s+", "", select, flags=re.I)
        depth, end = 0, len(body)
        for match in re.finditer(r"[()]|\bfrom\b", body, re.I):
            token = match.group(0).lower()
            if token == "(":
                depth += 1
            elif token == ")":
                depth -= 1
            elif depth == 0:
                end = match.start()
                break
        columns = []
        for item in top_level_split(body[:end]):
            alias = ALIAS.search(item)
            name = alias["alias"] if alias else item.split(".")[-1].strip('"` ')
            kind = known.get(name.lower(), "double") if not alias else "double"
            columns.append({"Name": name.lower(), "Type": kind})
        return columns

    def statement(self, sql: str) -> tuple[str, str, QueryResults | None]:
        """The statement's type and substatement type and the rows its reader gets; its effect in
        Glue is applied. Raises Failure for a statement Athena would end FAILED."""
        clean = LINE_COMMENT.sub("", QUERY_COMMENT.sub("", sql, count=1)).strip()
        if match := CTAS.match(clean):
            database, table = name_of(match["name"])
            properties = {
                key.lower(): value for key, value in PROPERTY.findall(match["properties"])
            }
            source = self.require_sources(match["select"])
            columns = self.select_columns(match["select"], source)
            self.create_table(database, table, properties.get("location", ""), columns)
            return "DML", "CREATE_TABLE_AS_SELECT", None
        if match := RENAME.match(clean):
            database, table = name_of(match["source"])
            target_database, target = name_of(match["target"])
            found = self.table(database, table)
            if found is None:
                raise Failure(f"TABLE_NOT_FOUND: Table '{database}.{table}' does not exist")
            if self.table(target_database, target) is not None:
                raise Failure(f"ALREADY_EXISTS: Table '{target_database}.{target}' already exists")
            table_input = {key: found[key] for key in TABLE_INPUT_KEYS if key in found}
            table_input["Name"] = target
            table_input["Parameters"] = dict(found.get("Parameters", {}))
            self.glue.create_table(target_database, target, table_input)
            self.glue.delete_table(database, table)
            return "DDL", "ALTER_TABLE", None
        if match := DROP.match(clean):
            database, table = name_of(match["name"])
            if self.table(database, table) is not None:
                self.glue.delete_table(database, table)
            elif not match["exists"]:
                raise Failure(f"TABLE_NOT_FOUND: Table '{database}.{table}' does not exist")
            return "DDL", "DROP_TABLE", None
        word = clean.split(None, 1)[0].lower() if clean else ""
        if word in ("create", "alter", "drop", "msck"):
            return "DDL", f"{word.upper()}_TABLE", None
        if word in ("show", "describe"):
            return "UTILITY", word.upper(), None
        return "DML", "SELECT", self.results(clean)

    def results(self, sql: str) -> QueryResults | None:
        """The rows of a SELECT, the header row first as Athena returns it."""
        self.require_sources(sql)
        if match := CONSTANT.match(sql):
            return QueryResults(rows(("_col0",), (match["value"],)), [column("_col0", "varchar")])
        if match := SELECT_ONE.match(sql):
            name = match["alias"] or "_col0"
            return QueryResults(rows((name,), ("1",)), [column(name, "integer")])
        if "as should_error" in sql.lower():
            failing = self.mode["test"] == "fail"
            values = ("1", "true", "true") if failing else ("0", "false", "false")
            names = ("failures", "should_warn", "should_error")
            info = [column("failures", "bigint"), column("should_warn", "boolean")]
            info.append(column("should_error", "boolean"))
            return QueryResults(rows(names, values), info)
        if COUNT.match(sql):
            count = str(self.setup.get("source_rows", 0))
            return QueryResults(rows(("_col0",), (count,)), [column("_col0", "bigint")])
        return None

    def start(self, request: dict[str, Any], execution: str) -> None:
        """A statement moto accepted: its effect, its rows and how GetQueryExecution answers it."""
        record = {
            "state": "SUCCEEDED",
            "reason": None,
            "result_configuration": "ResultConfiguration" in request,
            "workgroup": request.get("WorkGroup"),
        }
        try:
            record["type"], record["subtype"], results = self.statement(request["QueryString"])
            if results is not None:
                self.athena.query_results[execution] = results
        except Failure as failure:
            record["type"], record["subtype"] = "DML", "SELECT"
            record["state"], record["reason"] = "FAILED", str(failure)
        with self.lock:
            self.statements[execution] = record

    def execution(self, body: bytes) -> bytes:
        """moto's GetQueryExecution answer with the statement's type, state and output location."""
        answer = json.loads(body)
        execution = answer["QueryExecution"]
        record = self.statements.get(execution["QueryExecutionId"])
        if record is None:
            return body
        execution["StatementType"] = record["type"]
        execution["SubstatementType"] = record["subtype"]
        execution["Status"]["State"] = record["state"]
        if record["reason"]:
            execution["Status"]["StateChangeReason"] = record["reason"]
            execution["Status"]["AthenaError"] = {
                "ErrorCategory": 2,
                "Retryable": False,
                "ErrorMessage": record["reason"],
            }
        group = self.athena.get_work_group(execution.get("WorkGroup") or "")
        output = (group or {}).get("Configuration", {}).get("ResultConfiguration", {})
        if output.get("OutputLocation") and not record["result_configuration"]:
            location = output["OutputLocation"].rstrip("/")
            execution["ResultConfiguration"] = {
                "OutputLocation": f"{location}/{execution['QueryExecutionId']}.csv"
            }
        return json.dumps(answer).encode()


def scope_service(environ: dict[str, Any]) -> str:
    """The service a SigV4 request is signed for, from its credential scope."""
    authorization = environ.get("HTTP_AUTHORIZATION", "")
    match = re.search(r"Credential=[^/]+/[^/]+/[^/]+/([^/]+)/aws4_request", authorization)
    return match.group(1) if match else "unsigned"


def operation_of(environ: dict[str, Any], body: bytes) -> str:
    target = environ.get("HTTP_X_AMZ_TARGET")
    if target:
        return target.split(".")[-1]
    method, path = environ.get("REQUEST_METHOD", ""), environ.get("PATH_INFO", "")
    for known_method, pattern, name in DATAZONE_PATHS:
        if method == known_method and pattern.match(path):
            return name
    action = parse_qs(body.decode("utf-8", "replace")).get("Action")
    if action:
        return action[0]
    return f"{method} {path}"


class Recorder:
    """The WSGI layer over moto: the trail, the statements' effects, the control paths."""

    def __init__(self, application: Any, simulation: Simulation) -> None:
        self.application = application
        self.simulation = simulation

    def __call__(self, environ: dict[str, Any], start_response: Any) -> list[bytes]:
        length = int(environ.get("CONTENT_LENGTH") or 0)
        body = environ["wsgi.input"].read(length) if length else b""
        environ["wsgi.input"] = io.BytesIO(body)
        path = environ.get("PATH_INFO", "")
        if path.startswith("/_simulation/"):
            return self.control(path, body, start_response)
        service, operation = scope_service(environ), operation_of(environ, body)
        entry: dict[str, Any] = {"service": service, "operation": operation}
        request = {}
        if body[:1] == b"{":
            request = json.loads(body)
        if service == "datazone":
            status, answer = "501 Not Implemented", b'{"message":"no DataZone in the simulation"}'
            headers = [("Content-Type", "application/json"), ("x-amzn-ErrorType", "NotImplemented")]
        else:
            status, headers, answer = self.forward(environ)
        code = int(status.split()[0])
        if service == "athena" and operation == "StartQueryExecution" and code == 200:
            execution = json.loads(answer)["QueryExecutionId"]
            self.simulation.start(request, execution)
            record = self.simulation.statements[execution]
            first = " ".join(
                LINE_COMMENT.sub("", QUERY_COMMENT.sub("", request["QueryString"])).split()
            )
            entry["statement"] = first[:120]
            entry["workgroup"] = record["workgroup"]
            entry["result_configuration"] = record["result_configuration"]
            entry["outcome"] = record["state"]
        if service == "athena" and operation == "GetQueryExecution" and code == 200:
            answer = self.simulation.execution(answer)
        if "Name" in request and service == "glue":
            entry["name"] = request["Name"]
        entry["status"] = code
        with self.simulation.lock:
            self.simulation.trail.append(entry)
        headers = [(key, value) for key, value in headers if key.lower() != "content-length"]
        headers.append(("Content-Length", str(len(answer))))
        start_response(status, headers)
        return [answer]

    def forward(self, environ: dict[str, Any]) -> tuple[str, list[tuple[str, str]], bytes]:
        captured: dict[str, Any] = {}
        chunks: list[bytes] = []

        def capture(status: str, headers: list[tuple[str, str]], exc_info: Any = None) -> Any:
            captured["status"], captured["headers"] = status, headers
            return chunks.append

        result = self.application(environ, capture)
        try:
            chunks.extend(result)
        finally:
            if hasattr(result, "close"):
                result.close()
        return captured["status"], captured["headers"], b"".join(chunks)

    def control(self, path: str, body: bytes, start_response: Any) -> list[bytes]:
        simulation = self.simulation
        payload = json.loads(body) if body else {}
        if path == "/_simulation/reset":
            simulation.reset(payload)
            answer: Any = {"reset": True}
        elif path == "/_simulation/clear":
            simulation.clear()
            answer = {"cleared": True}
        elif path == "/_simulation/mode":
            simulation.mode.update(payload)
            answer = dict(simulation.mode)
        elif path == "/_simulation/trail":
            answer = list(simulation.trail)
        elif path == "/_simulation/events":
            answer = list(simulation.events)
        else:
            start_response("404 Not Found", [("Content-Length", "0")])
            return [b""]
        data = json.dumps(answer).encode()
        start_response(
            "200 OK", [("Content-Type", "application/json"), ("Content-Length", str(len(data)))]
        )
        return [data]


def listener_handler(simulation: Simulation) -> type[BaseHTTPRequestHandler]:
    class Listener(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            return

        def answer(self, code: int, payload: dict[str, Any], **headers: str) -> None:
            data = json.dumps(payload).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            for key, value in headers.items():
                self.send_header(key.replace("_", "-"), value)
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self) -> None:  # noqa: N802
            body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
            match = re.match(r"^/v2/domains/([^/?]+)/lineage/events$", self.path)
            if match is None:
                self.answer(404, {"message": f"no route {self.path}"})
                return
            authorization = self.headers.get("Authorization", "")
            signed = authorization.startswith("AWS4-HMAC-SHA256") and (
                "/datazone/aws4_request" in authorization
            )
            refused = simulation.mode["listener"] == "refuse"
            with simulation.lock:
                simulation.events.append(
                    {
                        "domain": match.group(1),
                        "signed": signed,
                        "bytes": len(body),
                        "answered": 403 if refused else 200,
                        "at": time.time(),
                        "event": json.loads(body),
                    }
                )
            if refused:
                self.answer(
                    403,
                    {"message": "User is not authorized to perform: datazone:PostLineageEvent"},
                    x_amzn_ErrorType="AccessDeniedException",
                )
            else:
                self.answer(200, {"id": uuid.uuid4().hex[:14], "domainId": match.group(1)})

    return Listener


def main() -> None:
    # A line per request on standard error would bury the simulation's own output.
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    simulation = Simulation()
    application = Recorder(DomainDispatcherApplication(create_backend_app), simulation)
    recorder = make_server("127.0.0.1", 0, application, True, request_handler=MotoRequestHandler)
    listener = ThreadingHTTPServer(("127.0.0.1", 0), listener_handler(simulation))
    for server in (recorder, listener):
        threading.Thread(target=server.serve_forever, daemon=True).start()
    ports = {"recorder": recorder.server_port, "listener": listener.server_port}
    print(json.dumps(ports), flush=True)
    sys.stdin.read()
    recorder.shutdown()
    listener.shutdown()


if __name__ == "__main__":
    main()
