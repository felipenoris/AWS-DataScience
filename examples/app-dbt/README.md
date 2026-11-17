# app-dbt

A dbt project run by a Bash task of a SageMaker workflow: Athena builds the model as an Iceberg table of
the project's database, and OpenLineage's dbt wrapper posts the run's lineage to the domain. The
application of the infrastructure repository's Stage 20, written after the template `examples/app-etl/`
and kept in that repository alone: it has no GitLab project and no release (the stage's decision 9). The
CI/CD CLI deploys it from a space into one Sandbox project, its single stage `dev`.

| Path | What it is |
|---|---|
| `manifest.yaml` | the application: the folders the CLI copies to the project's shared prefix, the two workflows, and the stage `dev` with the variables the workflows read |
| `workflows/app-dbt.yaml` | the workflow: `load`, a Glue job that writes the source table, then `transform`, dbt on the worker |
| `workflows/app-dbt-probe.yaml` | one inline Bash task that prints what the plan assumes of the worker and the AWS calls `transform` makes, each answer or refusal on one line |
| `glue/load.py` | the Glue job's script: the inbox's trades as the Iceberg table `trades` of the product database |
| `code/run-dbt.sh` | the `transform` task's command: dbt through the wrapper, the lineage configuration written for the run; copied to the archive's root |
| `src/app_dbt/` | the package the archive carries: the dbt project (`project/`), dbt Core's console script (`bin/dbt`), and the transformer of the datasets' names (`lineage.py`) |
| `code/app-dbt.zip` | the worker's archive, built by `package-task` and never committed |
| `scripts/dev-cli.sh` | the CI/CD CLI for the `dev` stage in a space, the template's copy |
| `samples/trades.csv` | synthetic trades, which the manifest copies to the workflow's inbox |
| `tests/` | pytest, offline; `tests/fixtures/` holds the events the simulation recorded, and `tests/simulation/` the simulation itself, outside pytest's collection |
| `pyproject.toml`, `uv.lock` | the project and its lock: dbt Core 1.11, `dbt-athena` 1.11 and `openlineage-dbt` 1.55, resolved under `exclude-newer` |

## The workflow

Every path is under the project's shared prefix, `{proj.connection.default.s3_shared.s3Uri}app-dbt/`:

| Task | Operator | What it does | Its lineage |
|---|---|---|---|
| `load` | `GlueJobOperator`, the job `app-dbt-{proj.id}` (Glue 6.0, two `G.1X` workers, the project's network connections), created or updated by the task | reads `inbox/` and writes the Iceberg table `trades` of `{env.PRODUCT_DATABASE}`, read back and counted | the Spark listener, the template's settings |
| `transform` | `BashOperator` on the worker, from `code/app-dbt.zip`; after `load` | `dbt build` through the wrapper: the model `notional_by_desk`, an Iceberg table Athena creates from `trades`, and a `not_null` test on its `desk` | the wrapper's events, posted by the `amazon_datazone_api` transport |

Each task is tried once (`retries: 0`). The worker extracts the archive to `/usr/local/airflow/dags`, and
`transform` starts `bash /usr/local/airflow/dags/run-dbt.sh` with every option in single quotes, so
neither the mode the extraction leaves nor a template lookup on a command ending in `.sh` plays a part.
The script:

1. copies the package's project to a folder of `mktemp -d`, since dbt writes `target/` and `logs/`
   beside the project it runs;
2. uses `app_dbt/bin/dbt` where it sits when the extraction kept its mode, else a copy marked executable:
   the wrapper starts `dbt` by name, and `package-task` removes console scripts;
3. reads the product database's location with `glue:GetDatabase`, the profile's `s3_data_dir`, under
   which the adapter places each Iceberg table;
4. writes `openlineage.yml` for the names' form, exports `OPENLINEAGE_CONFIG`, and runs the wrapper with
   `--project-dir` and `--profiles-dir` on the copy, printing the peak resident memory of the wrapper and
   of the dbt it starts.

The profile names no account and no `s3_staging_dir`: the workgroup's enforced output places every
result. The model drops a table by an Athena statement (`native_drop`), never by deleting its files, and
`persist_docs` writes the descriptions of `schema.yml` into the Glue table.

### The stage variables

| Variable | What it holds |
|---|---|
| `SUBNET_AZ1`, `SUBNET_AZ2` | the project's subnets, which name the Glue job's network connections |
| `ACCOUNT_ID` | the account of the Glue job's catalog and of the lineage's Glue names |
| `PRODUCT_DATABASE` | `app_dbt`, a literal: the database is created in the project before the first deploy, never by the application |
| `ATHENA_WORKGROUP` | the project's workgroup |
| `LINEAGE_DOMAIN` | the domain `transform` posts the events to |
| `LINEAGE_NAMES` | `as-built` or `glue-arn`, the form of the datasets' names |
| `LINEAGE_ENDPOINT` | the DataZone endpoint's URL, or `default` for the Region's |
| `LINEAGE_ATTEMPTS` | the attempts of every botocore client of the run, the transport's included, or `default` |

A stage variable is a parameter of the deployed workflow, filled from the shell of each `run`: a switch
turned between two runs is an `export` and a run, never a deploy. The CLI refuses an empty value, so a
switch at rest holds `default`.

### The lineage

| `LINEAGE_NAMES` | A dataset's namespace | Its name |
|---|---|---|
| `as-built` | `awsathena://athena.<region>.amazonaws.com` | `awsdatacatalog.<database>.<table>` |
| `glue-arn` | `arn:aws:glue:<region>:<account>:table` | `<database>/<table>` |

With `as-built`, the events go as the wrapper builds them. With `glue-arn`, the `transform` transport
hands each event to `app_dbt.lineage.GlueTableNames` before the post, which renames every Athena
dataset of the inputs, the outputs and each `columnLineage` input field. Either way each dataset keeps
its `symlinks` facet, which names `table/<database>/<table>` under `arn:aws:glue:<region>:<account>`.
A build posts six events after dbt ends, a `START` and an end for the dbt run, for the model and for
its test, under the job namespace `app-dbt` (`APP_DBT_NAMESPACE` replaces it by hand).

### Exit codes of `run-dbt.sh`

| Code | When |
|---|---|
| 2 | an option it does not know, one left out or without a value, or a `--names`, `--endpoint` or `--attempts` outside its forms |
| 3 | the product database has no location in Glue |
| 1 | `glue:GetDatabase` refused or unanswered, before dbt starts |
| dbt's | past those, the wrapper's code, which is dbt's: 1 when a model or a test fails |

A post the endpoint refuses, or never answers, leaves the code alone: the wrapper logs the warning with
the whole event and ends with dbt's code.

## Working on it

```bash
uv sync
uv run pytest
```

The tests run offline: `dbt parse` over the project through `bin/dbt`, with placeholder values and every
network path closed; each workflow's Bash command translated as the CLI translates it, rendered under
`StrictUndefined` with the stage's variables, and parsed by `bash -n`; the stage declaring every
`{env.NAME}` a workflow reads; `run-dbt.sh` over doubles of boto3 and of the wrapper; the transformer
over the recorded events; the Glue script over doubles; and the stored mode of each script. A script
is committed with the executable bit, `git update-index --chmod=+x <file>` where the file system keeps
none: `package-task` copies the mode into the archive.

The lint and the archive run from this folder with `awsds-workflows` at `1a50ceb`, the merge of its
pull request #27, whose rule `job` leaves a processing task's isolation to the task (Stage 20 step
6.4):

```bash
TOOL="awsds-workflows @ https://github.com/felipenoris/awsds-workflows/archive/1a50ceb15efe76abd0415758975467f89a11548b.zip"
uvx --from "$TOOL" awsds-workflows lint .
uvx --from "$TOOL" awsds-workflows package-task . code/app-dbt.zip --platform x86_64-manylinux_2_28 --include code/run-dbt.sh
python3 -c 'import sys, zipfile; z = zipfile.ZipFile(sys.argv[1]); print(len(z.infolist()), sum(i.file_size for i in z.infolist()), [oct(z.getinfo(n).external_attr >> 16) for n in ("run-dbt.sh", "app_dbt/bin/dbt")])' code/app-dbt.zip
```

The platform is `x86_64-manylinux_2_28`, since the compiled module of `openlineage-sql` asks for glibc
2.28. The archive leaves out boto3, botocore and PyYAML, which the worker carries, and holds under 250
MB unzipped. The check prints the entries, the unzipped bytes and `['0o100755', '0o100755']`.

### From a space

In a JupyterLab space of the project, Sandbox's egress raised with `GROUPS=mwaa` and the tree unpacked
with its archive, the values the manifest reads come from the space, the workgroup's name typed, then
the deploy and the runs:

```bash
git clone --depth 1 https://github.com/felipenoris/awsds-workflows /tmp/awsds-workflows
/opt/conda/bin/python /tmp/awsds-workflows/scripts/space_values.py > /tmp/space_values.json
eval "$(/opt/conda/bin/python -c 'import json; v = json.load(open("/tmp/space_values.json")); print("\n".join("export %s=%s" % p for p in (("DOMAIN_ID", v["DOMAIN_ID"]), ("DOMAIN_REGION", v["REGION"]), ("SUBNET_AZ1", v["SUBNET_AZ1"]), ("SUBNET_AZ2", v["SUBNET_AZ2"]), ("ACCOUNT_ID", v["ACCOUNT_ID"]))))')"
export DEV_PROJECT_NAME=<the project> ATHENA_WORKGROUP=<the project's workgroup>
export LINEAGE_DOMAIN="$DOMAIN_ID" LINEAGE_NAMES=as-built LINEAGE_ENDPOINT=default LINEAGE_ATTEMPTS=default
scripts/dev-cli.sh deploy --manifest manifest.yaml --targets dev --skip-validation --no-events
scripts/dev-cli.sh run --manifest manifest.yaml --targets dev --workflow app-dbt-probe
scripts/dev-cli.sh run --manifest manifest.yaml --targets dev --workflow app-dbt
```

By hand, the archive unpacked beside the space's own Python, under another job namespace; the dbt
command follows `--`:

```bash
mkdir -p /tmp/app-dbt-hand && python3 -m zipfile -e code/app-dbt.zip /tmp/app-dbt-hand
PYTHONPATH=/tmp/app-dbt-hand APP_DBT_NAMESPACE=app-dbt-by-hand bash /tmp/app-dbt-hand/run-dbt.sh --region us-west-2 --account "$ACCOUNT_ID" --database app_dbt --workgroup "$ATHENA_WORKGROUP" --domain "$LINEAGE_DOMAIN" --names "$LINEAGE_NAMES" -- debug
```

The archive's compiled modules are the worker's, so the space must run Python 3.12 on Linux x86_64;
the script's second line names the interpreter.

### The simulation

`tests/simulation/` runs the `transform` task against simulated services, with no AWS call, and
regenerates `tests/fixtures/`. It runs by hand, at each change of the lock or of `run-dbt.sh`:

```bash
uv run python tests/simulation/simulate.py --work <a scratch folder> --fixtures
```

It builds a worker's environment (CPython 3.12, `apache-airflow` 3.0.6 under its constraint file,
boto3 and botocore 1.43.1), moto's environment, and an archive for the host's platform, then runs each
case as the worker runs a Bash task's command: `bash -c "<command>"` in a folder of its own, the
archive's root first on `PYTHONPATH`. `services.py` puts moto's Athena, Glue, S3 and STS behind a
recorder that gives each Athena statement its effect in Glue, and stands a listener for the domain's
endpoint. The account is `000000000000`, which moto takes from `MOTO_ACCOUNT_ID`. The cases are the two
forms of the names, a missing database, both workflows' commands rendered, the runs by hand, the archive
at mode 644, the profile without the workgroup's read, the endpoint closed or refusing, and a failing
test; the script prints each one's exit code, seconds, calls, events, log and peak memory.
