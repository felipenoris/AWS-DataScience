# app-dbt

A dbt project run by a Bash task of a SageMaker workflow: Athena builds each model as an Iceberg table of
the project's database, and OpenLineage's dbt wrapper posts the run's lineage to the domain. The
application of the infrastructure repository's Stage 20, on the template `examples/app-etl/` with no
image, no job and no model. Its manifest holds three stages, one account each (the stage's decisions
7 (b) and 9 (b)): `dev`, the application's own Sandbox project, which the developer deploys to from a
space and the pipeline's `bundle` reads; and `staging` and `prod`, each account's deployment project,
`deploy-staging` and `deploy-production`, which the pipeline's legs deploy the release's bundle into. The
cycle an application on this template follows, from a space to Production, is
`docs/plan/runbooks/sagemaker-application.md` in the infrastructure repository.

| Path | What it is |
|---|---|
| `manifest.yaml` | the application: the folders the CLI copies to the project's shared prefix, the two workflows, the catalog block, and the three stages with the variables the workflows read |
| `workflows/app-dbt.yaml` | the workflow: `load`, a Glue job that writes the source table, then `transform`, dbt on the worker |
| `workflows/app-dbt-probe.yaml` | one inline Bash task that prints what the plan assumes of the worker and the AWS calls `transform` makes, each answer or refusal on one line |
| `glue/load.py` | the Glue job's script: the inbox's trades as the Iceberg table `trades` of the product database |
| `code/run-dbt.sh` | the `transform` task's command: dbt through the wrapper, the lineage configuration written for the run; copied to the archive's root |
| `src/app_dbt/` | the package the archive carries: the dbt project (`project/`), dbt Core's console script (`bin/dbt`), and the transformer of the datasets' names (`lineage.py`) |
| `code/app-dbt.zip` | the worker's archive, built by `package-task` (the pipeline's `build-task-code`, or by hand before a deploy from a space) and never committed |
| `product.json` | what a release's bundle carries from the `dev` project's catalog: the assets `trades` and `notional_by_desk`, and the metadata form `classification` |
| `scripts/check-catalog-export.py` | the release guard over the bundle's catalog, app-etl's script |
| `scripts/dev-cli.sh` | the CI/CD CLI for the `dev` stage in a space, app-etl's script; it gives the targets' names a placeholder |
| `samples/trades.csv` | synthetic trades, which the manifest copies to the workflow's inbox |
| `tests/` | pytest, offline; `tests/fixtures/` holds the events the simulation recorded, and `tests/simulation/` the simulation itself, outside pytest's collection |
| `.gitlab-ci.yml` | the pipeline, with the shared gates from `awsds/ci-gates` |
| `pyproject.toml`, `uv.lock` | the project and its lock: dbt Core 1.11, `dbt-athena` 1.11 and `openlineage-dbt` 1.55, resolved under `exclude-newer` for Linux and macOS |

No Terraform runs the application: the CI/CD CLI deploys it into a project in every account. What the
infrastructure repository's Stage 20 pass 8 gives it: in Sandbox, the `dev` project's role in
`sandbox/workflows/`'s `project_roles`, which grants the Glue task's `glue:GetJob`; in each target, the
database `app_dbt` in the deployment project, created by its `DataLake` environment before the first
deploy, the deploy role's read of the two tables' metadata (`deploy-project.tf`, and in Staging the Lake
Formation `DESCRIBE` of `staging-test.tf`), the chains in `terraform-live/<env>/chains/`, and an `athena`
interface endpoint in the account's egress slice (the stage's decision 15).

## The workflow

Every path is under the project's shared prefix, `{proj.connection.default.s3_shared.s3Uri}app-dbt/`:

| Task | Operator | What it does | Its lineage |
|---|---|---|---|
| `load` | `GlueJobOperator`, the job `app-dbt-{proj.id}` (Glue 6.0, two `G.1X` workers, the project's network connections), created or updated by the task | reads `inbox/` and writes the Iceberg table `trades` of `{env.PRODUCT_DATABASE}`, read back and counted | the Spark listener, the template's settings |
| `transform` | `BashOperator` on the worker, from `code/app-dbt.zip`; after `load` | `dbt build` through the wrapper: the models `notional_by_desk`, an Iceberg table Athena creates from `trades`, and `notional_by_desk_prod`, one from `trades_notional`, the resource link of the project's subscription to Production's listing, each with a `not_null` test on its `desk` | the wrapper's events, posted by the `amazon_datazone_api` transport |

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
| `PRODUCT_DATABASE` | `app_dbt`, a literal: the database is created in each project before its first deploy, never by the application |
| `LINEAGE_DOMAIN` | the domain `transform` posts the events to |
| `LINEAGE_NAMES` | `as-built` or `glue-arn`, the form of the datasets' names |
| `LINEAGE_ENDPOINT` | the DataZone endpoint's URL, or `default` for the Region's |
| `LINEAGE_ATTEMPTS` | the attempts of every botocore client of the run, the transport's included, or `default` |
| `LINEAGE_NAMESPACE` | the job namespace of the run's events, `app-dbt-<stage>`: `app-dbt-dev` exported in `dev`, `app-dbt-staging` and `app-dbt-prod` written in the targets |

In `dev` every value but the literal comes from the shell of the space. A target holds `${DOMAIN_ID}` for
`LINEAGE_DOMAIN`, and its switches and its namespace as literals, `as-built`, `default` and
`app-dbt-<stage>`; its leg fills the subnets and the account from the deployment project. A stage
variable is a parameter of the deployed workflow, filled from the shell of each `run`: a switch turned
between two runs in `dev` is an `export` and a run, never a deploy. The CLI refuses an empty value, so a
switch at rest holds `default`. Every stage declares every variable a workflow reads, since the deploy
resolves every workflow the manifest names.

The Athena workgroup is no stage variable. Both workflows name
`{proj.connection.project.athena.workgroupName}`, the workgroup of the `project.athena` connection that
every project's Tooling environment creates, `workgroup-<project id>-<Tooling environment id>`, and the
CLI resolves it at the deploy in each stage's project (the infrastructure repository's Stage 20 decision
17 (b)).

### The lineage

| `LINEAGE_NAMES` | A dataset's namespace | Its name |
|---|---|---|
| `as-built` | `awsathena://athena.<region>.amazonaws.com` | `awsdatacatalog.<database>.<table>` |
| `glue-arn` | `arn:aws:glue:<region>:<account>:table` | `<database>/<table>` |

With `as-built`, the events go as the wrapper builds them. With `glue-arn`, the `transform` transport
hands each event to `app_dbt.lineage.GlueTableNames` before the post, which renames every Athena
dataset of the inputs, the outputs and each `columnLineage` input field. Either way each dataset keeps
its `symlinks` facet, which names `table/<database>/<table>` under `arn:aws:glue:<region>:<account>`.
A build posts its events after dbt ends, a `START` and an end for the dbt run, for each model and for
each test, under the stage's job namespace, `LINEAGE_NAMESPACE` (the infrastructure repository's Stage 20
decision 16 (c)): each stage's runs are a job of their own in the domain every account posts to.
`run-dbt.sh` by hand reads `app-dbt` unless `--namespace` names another.

### Exit codes of `run-dbt.sh`

| Code | When |
|---|---|
| 2 | an option it does not know, one left out or without a value, or a `--names`, `--endpoint`, `--attempts` or `--namespace` outside its forms |
| 3 | the product database has no location in Glue |
| 1 | `glue:GetDatabase` refused or unanswered, before dbt starts |
| dbt's | past those, the wrapper's code, which is dbt's: 1 when a model or a test fails |

A post the endpoint refuses, or never answers, leaves the code alone: the wrapper logs the warning with
the whole event and ends with dbt's code.

## The catalog

`bundle` exports what the `dev` project owns beside the tag's files (`catalog/catalog_export.json`), and
each deploy imports it into the stage's project, listing nothing (`skipPublish`): no task of this
application publishes. The `dev` project's assets are the two tables' inventory assets, `trades` and
`notional_by_desk`, created by the project's source over `app_dbt` and curated there by the developer:
their descriptions, their README and the form `classification`. `product.json` declares what a release
carries, and `scripts/check-catalog-export.py` fails a bundle with a resource outside it, without either
asset, or with no export. A resource the developer adds to an asset in the `dev` project, a glossary term
for one, joins `product.json` in the same merge request, and anything else the project owns fails the
release: a model over what only `dev` holds, a subscription's resource link among them, stays on a
branch no tag carries, and its table's asset leaves the project before a tag.

The import matches an asset by its external identifier, then by its name, so an asset's name is unique
within a deployment project, where every application's assets sit. A target's first import creates no
asset (`SUP-369` in the infrastructure repository): the deploy admits it, the leg's run writes the two
tables, and the leg's catalog job runs the project's source over `app_dbt` and deploys the same bundle
again, which revises both assets with `dev`'s metadata.

## Working on it

```bash
uv sync
uv run pytest
```

The tests run offline: `dbt parse` over the project through `bin/dbt`, with placeholder values and every
network path closed; each workflow's Bash command translated as the CLI translates it, rendered under
`StrictUndefined` with each stage's variables, and parsed by `bash -n`; every stage declaring every
`{env.NAME}` a workflow reads; the manifest's stages against what the infrastructure repository's legs
fill; `run-dbt.sh` over doubles of boto3 and of the wrapper; the transformer over the recorded events;
the Glue script over doubles; the release guard over bundles built in a temporary folder; and the stored
mode of each script. A script is committed with the executable bit, `git update-index --chmod=+x <file>`
where the file system keeps none: `package-task` copies the mode into the archive.

The lock resolves for Linux, where the worker and the pipeline run, and macOS, where the tests run on a
laptop (`[tool.uv] environments`). The gates' `pip-audit` fails when it audits fewer packages than the
runtime export pins, and pip-audit 2.10.1 skips a pin whose marker its Linux runner does not match.

The lint and the archive run from this folder with `awsds-workflows` at `4401f91`, the merge of its
pull request #29, whose rule `operador` refuses the native notebook operator by name (Stage 8 5.6),
after #28's `CLI_VARIABLES` admitted the project's Athena workgroup (Stage 20 decision 17 (b)) and
#27's rule `job` left a processing task's isolation to the task (step 6.4); the pipeline pins the same
commit:

```bash
TOOL="awsds-workflows @ https://github.com/felipenoris/awsds-workflows/archive/4401f91ffdf3b742c231e08bfe3443b05de4afec.zip"
uvx --from "$TOOL" awsds-workflows lint .
uvx --from "$TOOL" awsds-workflows package-task . code/app-dbt.zip --platform x86_64-manylinux_2_28 --include code/run-dbt.sh
python3 -c 'import sys, zipfile; z = zipfile.ZipFile(sys.argv[1]); print(len(z.infolist()), sum(i.file_size for i in z.infolist()), [oct(z.getinfo(n).external_attr >> 16) for n in ("run-dbt.sh", "app_dbt/bin/dbt")])' code/app-dbt.zip
```

The platform is `x86_64-manylinux_2_28`, since the compiled module of `openlineage-sql` asks for glibc
2.28. The archive leaves out boto3, botocore and PyYAML, which the worker carries, and holds under 250
MB unzipped. The check prints the entries, the unzipped bytes and `['0o100755', '0o100755']`.

### From a space

In a JupyterLab space of the application's `dev` project, Sandbox's egress raised with `GROUPS=mwaa` and
the tree unpacked with its archive, the values the manifest reads come from the space, the project's name
typed, then the deploy and the runs:

```bash
git clone --depth 1 https://github.com/felipenoris/awsds-workflows /tmp/awsds-workflows
/opt/conda/bin/python /tmp/awsds-workflows/scripts/space_values.py > /tmp/space_values.json
eval "$(/opt/conda/bin/python -c 'import json; v = json.load(open("/tmp/space_values.json")); print("\n".join("export %s=%s" % p for p in (("DOMAIN_ID", v["DOMAIN_ID"]), ("DOMAIN_REGION", v["REGION"]), ("SUBNET_AZ1", v["SUBNET_AZ1"]), ("SUBNET_AZ2", v["SUBNET_AZ2"]), ("ACCOUNT_ID", v["ACCOUNT_ID"]))))')"
export DEV_PROJECT_NAME=<the dev project>
export LINEAGE_DOMAIN="$DOMAIN_ID" LINEAGE_NAMES=as-built LINEAGE_ENDPOINT=default LINEAGE_ATTEMPTS=default
export LINEAGE_NAMESPACE=app-dbt-dev
scripts/dev-cli.sh deploy --manifest manifest.yaml --targets dev --skip-validation --no-events
scripts/dev-cli.sh run --manifest manifest.yaml --targets dev --workflow app-dbt-probe
scripts/dev-cli.sh run --manifest manifest.yaml --targets dev --workflow app-dbt
```

By hand, the archive unpacked beside the space's own Python, under another job namespace, the
workgroup typed as the project's `project.athena` connection names it; the dbt command follows `--`:

```bash
mkdir -p /tmp/app-dbt-hand && python3 -m zipfile -e code/app-dbt.zip /tmp/app-dbt-hand
export ATHENA_WORKGROUP=<the project's workgroup>
PYTHONPATH=/tmp/app-dbt-hand bash /tmp/app-dbt-hand/run-dbt.sh --region us-west-2 --account "$ACCOUNT_ID" --database app_dbt --workgroup "$ATHENA_WORKGROUP" --domain "$LINEAGE_DOMAIN" --names "$LINEAGE_NAMES" --namespace app-dbt-by-hand -- debug
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

## The pipeline

| Ref | Jobs | Runner |
|---|---|---|
| any branch | `test` (`uv sync --locked`, ruff, pytest, the workflow lint), `secret_detection` and its gate, `pip-audit` | the test runner, no AWS identity |
| a tag `v<semver>` | `test`, `pip-audit`; `build-task-code` (the worker's archive, its two modes and its sizes checked); `bundle` (the release's bundle, made from the tag's files and the `dev` project's catalog, held to `product.json`; nothing is deployed in Sandbox); `store-bundle` (the bundle to `awsds-prod-releases`); `release` (the tag's GitLab release); the promotion: `staging-gate` (manual), `staging-check` (Staging's `egress/` with its `athena` endpoint, the user's to raise, and its deployment project), `staging-deploy` (the CLI's deploy into the project), `staging-test` (the probe's chain, then `app-dbt`'s, and both tables' metadata), `staging-catalog` (the second import), `production-check` (Production's project and the deploy role's membership), `production-gate` (manual), `production-deploy` (the `athena` endpoint of `production/workloads-egress/`, then the CLI's deploy, whose bootstrap runs `app-dbt`), `production-catalog` (the second import, whose deploy runs `app-dbt` again) | the test runner, the build runner for `store-bundle` and `release`, and the deploy runner for `bundle` and the promotion |

A release is a tag `v<major>.<minor>.<patch>` on `main`, which only a Maintainer can create: the tag is
protected, and that protection is the release gate. A tag whose bundle fails gets no release, and the
release's first run is Staging's leg: the pipeline deploys nothing in Sandbox.

`bundle` runs as `awsds-deploy-sandbox-test`, a member of the `dev` project, and reads the GitLab
project's CI/CD variables `DOMAIN_ID`, `DOMAIN_REGION` and `DEV_PROJECT_NAME`. The CLI refuses a manifest
with an unset `${VAR}`, so the job gives every name it has no value for a placeholder. It fails on a
missing include, on the CLI's *"Failed to get project connections"*, and on a bundle the guard refuses.
The bundle's SHA256 goes down the pipeline as a dotenv report, and the release's notes name it with the
bundle's object.

The promotion runs on the deploy runner, each job cloning `awsds/infrastructure` with the job token, where
the scripts it calls live. `scripts/deploy-application.py` extracts the bundle beside the tag's manifest,
fills the stage's variables from the deployment project's Tooling environment, runs the CLI's `deploy`
and records the stage's variables for the chains. The `transform` task queries Athena from the deployment
project's subnets, which reach a service through an interface endpoint of the account's egress slice
alone, so `staging-check` and `production-deploy` ask EC2 for an available endpoint tagged
`awsds-staging-athena` and `awsds-prod-workloads-athena`, which each slice's list holds since Stage 20
decision 15 (a) and `check-egress.py` reads with the rest. The legs deploy with no `--image-uri`: the
release follows the infrastructure repository's change that teaches the script a second application
(Stage 20 step 8.1). A target's workgroup comes from its project's `project.athena` connection, which
the CLI resolves at the deploy (Stage 20 decision 17 (b)). Nothing is torn down: Staging's `make down` is
the user's. The jobs need the hub, the deploy runner, Staging's `egress/` and
`production/workloads-egress/`, each with its `athena` endpoint.
