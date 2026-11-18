"""app-dbt's transform task run against simulated services, with no AWS call (the infrastructure
repository's Stage 20, step 1.3).

    uv run python tests/simulation/simulate.py --work <folder> [--archive <zip>] [--only 1,2]
        [--fixtures]

Run from the application's folder; pytest does not collect this folder. In --work it builds:

- the worker's environment: CPython 3.12, apache-airflow 3.0.6 under its constraint file, then
  boto3 and botocore 1.43.1, the worker's versions;
- the services' environment, moto[server] 5.2.5, where services.py runs;
- the task's archive, built by package-task for this host's platform with run-dbt.sh at its root,
  unless --archive names one; it is extracted keeping each file's mode, again at mode 644 as
  `python3 -m zipfile -e` leaves it, and again with the profile's skip_workgroup_check set.

Each case runs as the worker runs a Bash task: `bash -c "<command>"` in a folder of its own,
under an environment that holds only what the case names, the archive's root first on PYTHONPATH,
every AWS client pointed at the recorder through AWS_ENDPOINT_URL, and the lineage endpoint at the
listener or at a closed port. A case starts in a fresh account or follows the one before it. The
script prints one row per case and writes each case's log, trail and events under --work/cases/;
--fixtures writes the events of the first two builds to tests/fixtures/, the work folder's paths
replaced.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import zipfile
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

APPLICATION = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(APPLICATION / "tests"))

import rendering  # noqa: E402

TOOL = (
    "awsds-workflows @ https://github.com/felipenoris/awsds-workflows/archive/"
    "1a50ceb15efe76abd0415758975467f89a11548b.zip"
)
AIRFLOW = "apache-airflow==3.0.6"
CONSTRAINTS = (
    "https://raw.githubusercontent.com/apache/airflow/constraints-3.0.6/constraints-3.12.txt"
)
WORKER_AWS = ("boto3==1.43.1", "botocore==1.43.1")
SERVICES = ("moto[server]==5.2.5", "boto3==1.43.1", "botocore==1.43.1")

ACCOUNT = "000000000000"
REGION = rendering.RESOLVED["domain.region"]
DOMAIN = rendering.RESOLVED["domain.id"]
DATABASE = "app_dbt"
WORKGROUP = rendering.RESOLVED["proj.connection.project.athena.workgroupName"]
LOCATION = "s3://simulated-bucket/simulated-domain/simulated-project/dev/data/catalogs/"
OUTPUT = "s3://simulated-bucket/simulated-domain/simulated-project/dev/sys/athena/"
SOURCE_COLUMNS = [
    ("trade_date", "date"),
    ("desk", "string"),
    ("instrument", "string"),
    ("quantity", "int"),
    ("price", "double"),
]
DAGS = "/usr/local/airflow/dags/"

# The lines a case's log is read for, each counted.
DECISIVE = (
    "run-dbt.sh: ",
    "Running with dbt=",
    "Registered adapter:",
    "Done. PASS=",
    "Successfully posted a LineageEvent",
    "Emitted ",
    "Underlying dbt execution returned",
    "OpenLineage client failed to emit event",
    "does not support timeout",
    "Completed with",
    "REFUSED",
    "Traceback",
)


@dataclass
class Context:
    work: Path
    worker: Path
    trees: dict[str, Path]
    recorder: str
    listener: str
    closed: str


@dataclass
class Case:
    name: str
    command: Callable[[Context, Path], str]
    follows: bool = False
    with_database: bool = True
    with_source: bool = True
    listener: str = "answer"
    test: str = "pass"
    env: dict[str, str] = field(default_factory=dict)
    tree: str = "modes"


def run(command: list[str], **options: Any) -> None:
    print("+", shlex.join(command), flush=True)
    subprocess.run(command, check=True, **options)


def environment(path: Path, *installs: tuple[tuple[str, ...], str | None]) -> Path:
    """A CPython 3.12 environment at `path`, each install run in order, built once."""
    python = path / "bin" / "python"
    if python.exists():
        return python
    run(["uv", "venv", "--python", "3.12", str(path)])
    for packages, constraint in installs:
        command = ["uv", "pip", "install", "--python", str(python), *packages]
        if constraint:
            command += ["--constraints", constraint]
        run(command)
    return python


def extract(archive: Path, folder: Path, keep_modes: bool) -> Path:
    if folder.exists():
        shutil.rmtree(folder)
    if not keep_modes:
        run([sys.executable, "-m", "zipfile", "-e", str(archive), str(folder)])
        return folder
    with zipfile.ZipFile(archive) as handle:
        for info in handle.infolist():
            path = handle.extract(info, folder)
            mode = info.external_attr >> 16
            if mode and not info.is_dir():
                os.chmod(path, mode & 0o7777)
    return folder


def skip_workgroup_check(folder: Path) -> Path:
    profile = folder / "app_dbt" / "project" / "profiles.yml"
    text = profile.read_text(encoding="utf-8")
    edited = text.replace(
        "      threads: 1\n", "      threads: 1\n      skip_workgroup_check: true\n"
    )
    if edited == text:
        raise SystemExit(f"no 'threads: 1' line to follow in {profile}")
    profile.write_text(edited, encoding="utf-8")
    return folder


def closed_port() -> int:
    """A local port nothing listens on."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


class Services:
    """services.py in its environment, and its control paths."""

    def __init__(self, python: Path) -> None:
        env = {
            "PATH": os.environ["PATH"],
            "HOME": os.environ["HOME"],
            "MOTO_ACCOUNT_ID": ACCOUNT,
            "NO_PROXY": "127.0.0.1,localhost",
        }
        script = Path(__file__).with_name("services.py")
        self.process = subprocess.Popen(
            [str(python), "-I", str(script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            env=env,
            text=True,
        )
        ports = json.loads(self.process.stdout.readline())
        self.recorder = f"http://127.0.0.1:{ports['recorder']}"
        self.listener = f"http://127.0.0.1:{ports['listener']}"
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def call(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        data = None if payload is None else json.dumps(payload).encode()
        request = urllib.request.Request(f"{self.recorder}/_simulation/{path}", data=data)
        with self.opener.open(request, timeout=30) as answer:
            return json.loads(answer.read())

    def stop(self) -> None:
        self.process.stdin.close()
        self.process.wait(timeout=30)


def stage_parameters(listener: str) -> dict[str, str]:
    """The run's parameters: the dev stage's environment_variables, each ${VAR} given the value
    the simulation stands for."""
    values = {
        "SUBNET_AZ1": "subnet-simulated-az1",
        "SUBNET_AZ2": "subnet-simulated-az2",
        "ACCOUNT_ID": ACCOUNT,
        "LINEAGE_DOMAIN": DOMAIN,
        "LINEAGE_NAMES": "as-built",
        "LINEAGE_ENDPOINT": listener,
        "LINEAGE_ATTEMPTS": "default",
        "LINEAGE_NAMESPACE": "app-dbt-dev",
    }
    parameters = {}
    for name, value in rendering.stage_variables().items():
        match = re.fullmatch(r"\$\{(\w+)\}", str(value))
        parameters[name] = values[match.group(1)] if match else str(value)
    return parameters


def rendered(workflow: str, task: str) -> Callable[[Context, Path], str]:
    def command(context: Context, tree: Path) -> str:
        for dag, name, text in rendering.bash_commands():
            if (dag, name) == (workflow, task):
                result = rendering.render(text, stage_parameters(context.listener))
                return result.replace(DAGS, f"{tree}/")
        raise SystemExit(f"no Bash task {task} in the workflow {workflow}")

    return command


def script(
    names: str = "as-built",
    endpoint: str = "listener",
    attempts: str | None = "default",
    database: str = DATABASE,
    namespace: str | None = None,
    after: tuple[str, ...] = (),
) -> Callable[[Context, Path], str]:
    """run-dbt.sh started as the task starts it, each option given."""

    def command(context: Context, tree: Path) -> str:
        words = ["bash", f"{tree}/run-dbt.sh", "--region", REGION, "--account", ACCOUNT]
        words += ["--database", database, "--workgroup", WORKGROUP, "--domain", DOMAIN]
        words += ["--names", names, "--endpoint", getattr(context, endpoint)]
        if attempts is not None:
            words += ["--attempts", attempts]
        if namespace is not None:
            words += ["--namespace", namespace]
        if after:
            words += ["--", *after]
        return shlex.join(words)

    return command


CASES = [
    Case("A first `dbt build`, the names as built", script()),
    Case("A second build, `--names glue-arn`", script(names="glue-arn"), follows=True),
    Case("A database Glue does not hold", script(), with_database=False),
    Case("The probe workflow's command, rendered", rendered("app-dbt-probe", "probe")),
    Case("The `transform` task's command, rendered", rendered("app-dbt", "transform")),
    Case(
        "By hand, `-- debug`",
        script(attempts=None, namespace="app-dbt-by-hand", after=("debug",)),
        follows=True,
    ),
    Case(
        "By hand, `-- run`",
        script(attempts=None, namespace="app-dbt-by-hand", after=("run",)),
        follows=True,
    ),
    Case("Every file of the archive at mode 644", script(), tree="644"),
    Case("The profile with `skip_workgroup_check: true`", script(), follows=True, tree="skip"),
    Case("The endpoint's port closed, `--attempts 1`", script(endpoint="closed", attempts="1")),
    Case(
        "The endpoint's port closed, botocore's default attempts",
        script(endpoint="closed"),
        follows=True,
    ),
    Case("The endpoint answering 403", script(), listener="refuse"),
    Case("A test that fails", script(), test="fail"),
]


def case_environment(context: Context, folder: Path, case: Case) -> dict[str, str]:
    env = {
        "PATH": f"{context.worker}/bin:/opt/homebrew/bin:/usr/bin:/bin",
        "PYTHONPATH": str(context.trees[case.tree]),
        "HOME": str(folder / "home"),
        "TMPDIR": str(folder / "tmp") + "/",
        "LANG": "en_US.UTF-8",
        "AWS_REGION": REGION,
        "AWS_DEFAULT_REGION": REGION,
        "AWS_ACCESS_KEY_ID": "testing",
        "AWS_SECRET_ACCESS_KEY": "testing",
        "AWS_SESSION_TOKEN": "testing",
        "AWS_ENDPOINT_URL": context.recorder,
        "AWS_CONFIG_FILE": str(folder / "absent-config"),
        "AWS_SHARED_CREDENTIALS_FILE": str(folder / "absent-credentials"),
        "AWS_EC2_METADATA_DISABLED": "true",
        "NO_PROXY": "127.0.0.1,localhost",
    }
    env.update(case.env)
    return env


def decisive(log: str) -> dict[str, list[Any]]:
    """Each decisive kind of line: how many the log holds and the first, cut at 300 characters."""
    found: dict[str, list[Any]] = {}
    for line in log.splitlines():
        for marker in DECISIVE:
            if marker in line:
                entry = found.setdefault(marker, [0, line.strip()[:300]])
                entry[0] += 1
    return found


def run_case(number: int, case: Case, context: Context, services: Services) -> dict[str, Any]:
    slug = re.sub(r"[^a-z0-9]+", "-", case.name.lower()).strip("-")[:48]
    folder = context.work / "cases" / f"{number:02d}-{slug}"
    if folder.exists():
        shutil.rmtree(folder)
    for part in ("home", "tmp", "task"):
        (folder / part).mkdir(parents=True)
    if case.follows:
        services.call("clear", {})
    else:
        services.call(
            "reset",
            {
                "database": DATABASE,
                "location": LOCATION,
                "workgroup": WORKGROUP,
                "output": OUTPUT,
                "source": "trades",
                "source_columns": SOURCE_COLUMNS,
                "source_rows": source_rows(),
                "with_database": case.with_database,
                "with_source": case.with_source,
            },
        )
    services.call("mode", {"listener": case.listener, "test": case.test})
    command = case.command(context, context.trees[case.tree])
    env = case_environment(context, folder, case)
    bash = shutil.which("bash", path=env["PATH"])
    started = datetime.now(UTC)
    clock = time.monotonic()
    with open(folder / "log.txt", "wb") as log:
        done = subprocess.run(
            [bash, "-c", command],
            cwd=folder / "task",
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            timeout=900,
        )
    seconds = time.monotonic() - clock
    keep_temporary_folders(folder)
    trail = services.call("trail")
    events = services.call("events")
    text = (folder / "log.txt").read_text(encoding="utf-8", errors="replace")
    peak = re.search(r"peak memory (\d+) kB", text)
    (folder / "command.txt").write_text(command + "\n", encoding="utf-8")
    (folder / "trail.json").write_text(json.dumps(trail, indent=2) + "\n", encoding="utf-8")
    (folder / "events.json").write_text(json.dumps(events, indent=2) + "\n", encoding="utf-8")
    return {
        "number": number,
        "name": case.name,
        "started": started.strftime("%H:%M:%S"),
        "exit": done.returncode,
        "seconds": round(seconds, 1),
        "calls": len(trail),
        "operations": [f"{entry['service']}:{entry['operation']}" for entry in trail],
        "statements": [entry["statement"] for entry in trail if "statement" in entry],
        "events": len(events),
        "signed": sum(1 for event in events if event["signed"]),
        "refused": sum(1 for event in events if event["answered"] != 200),
        "log_bytes": len(text.encode()),
        "log_lines": len(text.splitlines()),
        "peak_kb": int(peak.group(1)) if peak else None,
        "decisive": decisive(text),
        "folder": str(folder),
    }


def keep_temporary_folders(folder: Path) -> None:
    """Each folder the case's mktemp made outside its TMPDIR, moved into the case's folder: macOS
    mktemp takes the user's temporary folder before TMPDIR, where the worker's takes TMPDIR."""
    log = (folder / "log.txt").read_text(encoding="utf-8", errors="replace")
    for path in sorted(set(re.findall(r"/var/folders/\S+?/T/tmp\.[A-Za-z0-9]+", log))):
        if Path(path).is_dir():
            (folder / "mktemp").mkdir(exist_ok=True)
            shutil.move(path, folder / "mktemp" / Path(path).name)


def source_rows() -> int:
    lines = (APPLICATION / "samples" / "trades.csv").read_text(encoding="utf-8").splitlines()
    return len([line for line in lines[1:] if line.strip()])


def row(result: dict[str, Any]) -> str:
    events = str(result["events"])
    if result["events"] and result["refused"] == result["events"]:
        events += ", each refused"
    elif result["events"]:
        events += f", {result['signed']} signed"
    peak = f"{result['peak_kb']:,}" if result["peak_kb"] else "not read"
    log = f"{result['log_bytes']:,} and {result['log_lines']}"
    cells = [result["name"], result["exit"], result["seconds"], result["calls"], events, log, peak]
    return "| " + " | ".join(str(cell) for cell in cells) + " |"


def scrub(text: str, context: Context) -> str:
    """The work folder's paths replaced, so that no path of this machine reaches a fixture."""
    for path, placeholder in ((context.work.resolve(), "<work>"), (context.work, "<work>")):
        text = text.replace(str(path), placeholder)
    return text


def write_fixtures(results: list[dict[str, Any]], context: Context) -> None:
    fixtures = APPLICATION / "tests" / "fixtures"
    for number, name in ((1, "events-as-built.json"), (2, "events-glue-arn.json")):
        result = next(item for item in results if item["number"] == number)
        events = json.loads((Path(result["folder"]) / "events.json").read_text(encoding="utf-8"))
        text = scrub(json.dumps([entry["event"] for entry in events], indent=2), context)
        leftovers = re.findall(r"/(?:Users|private|tmp|var/folders)/[^\s\"]*", text)
        accounts = set(re.findall(r"(?<![0-9A-Za-z_-])[0-9]{12}(?![0-9A-Za-z_-])", text))
        if leftovers or accounts - {ACCOUNT}:
            raise SystemExit(f"{name}: a path or an account remains: {leftovers} {accounts}")
        (fixtures / name).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {fixtures / name}: {len(events)} event(s)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--platform", default="aarch64-apple-darwin")
    parser.add_argument("--only", help="the cases to run, by number, comma-separated")
    parser.add_argument("--fixtures", action="store_true")
    arguments = parser.parse_args()
    work = arguments.work.resolve()
    work.mkdir(parents=True, exist_ok=True)

    print("start", datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"), flush=True)
    worker = environment(work / "worker", ((AIRFLOW,), CONSTRAINTS), (WORKER_AWS, None))
    services_python = environment(work / "services", (SERVICES, None))
    archive = arguments.archive
    if archive is None:
        archive = work / "app-dbt-host.zip"
        command = ["uvx", "--from", TOOL, "awsds-workflows", "package-task", ".", str(archive)]
        command += ["--platform", arguments.platform, "--include", "code/run-dbt.sh"]
        run(command, cwd=APPLICATION)
    trees = {
        "modes": extract(archive, work / "dags", keep_modes=True),
        "644": extract(archive, work / "dags-644", keep_modes=False),
        "skip": skip_workgroup_check(extract(archive, work / "dags-skip", keep_modes=True)),
    }

    services = Services(services_python)
    context = Context(
        work=work,
        worker=worker.parent.parent,
        trees=trees,
        recorder=services.recorder,
        listener=services.listener,
        closed=f"http://127.0.0.1:{closed_port()}",
    )
    selected = {int(item) for item in arguments.only.split(",")} if arguments.only else None
    results = []
    try:
        for number, case in enumerate(CASES, start=1):
            if selected is None or number in selected:
                print(f"case {number}: {case.name}", flush=True)
                results.append(run_case(number, case, context, services))
    finally:
        services.stop()
    print("end", datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"))

    (work / "results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(
        "| Case | Exit code | Seconds | AWS calls | Events the listener received "
        "| Task log, bytes and lines | Peak memory, kB |"
    )
    print("|---|---|---|---|---|---|---|")
    for result in results:
        print(row(result))
    if arguments.fixtures:
        write_fixtures(results, context)


if __name__ == "__main__":
    main()
