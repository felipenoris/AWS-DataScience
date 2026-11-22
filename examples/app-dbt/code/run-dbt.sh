#!/usr/bin/env bash
# The transform task of app-dbt: dbt over the package's project through OpenLineage's wrapper, which
# starts dbt and posts the run's events to the domain (the infrastructure repository's Stage 20).
#
#   bash run-dbt.sh --region R --account A --database D --workgroup W --domain DZ --names as-built|glue-arn \
#       [--endpoint URL|default] [--attempts N|default] [--namespace NAME] [-- dbt command and options]
#
# The workflow's task passes every option (workflows/app-dbt.yaml); by hand, --endpoint and --attempts
# may be left out and read `default`, and --namespace, the job namespace of the run's events, reads
# `app-dbt`. The dbt command is `build` when none follows `--`. An unknown option, a missing one, one
# without a value, or a --names, --endpoint, --attempts or --namespace outside its forms exits 2; a
# product database Glue gives no location exits 3; a refused glue:GetDatabase exits 1; past that, the
# exit code is the wrapper's, which is dbt's.
#
# The worker extracts the archive to /usr/local/airflow/dags and starts the task in a folder of its own,
# PYTHONPATH naming the archive's root first: python3 imports the package app_dbt and the wrapper from
# the archive, and boto3 and PyYAML from the worker's own packages. The script calls python3, mktemp,
# cp, chmod and dirname, and no aws client, which the worker does not carry. The operator renders the
# task's command, never this file, which holds no template.
set -euo pipefail

usage="usage: run-dbt.sh --region R --account A --database D --workgroup W --domain DZ --names as-built|glue-arn [--endpoint URL|default] [--attempts N|default] [--namespace NAME] [-- dbt command]"

refuse() {
  echo "run-dbt.sh: $1" >&2
  echo "$usage" >&2
  exit 2
}

region="" account="" database="" workgroup="" domain="" names="" endpoint=default attempts=default
namespace=app-dbt
while [ "$#" -gt 0 ]; do
  case "$1" in
    --)
      shift
      break
      ;;
    --region | --account | --database | --workgroup | --domain | --names | --endpoint | --attempts | --namespace)
      if [ "$#" -lt 2 ] || [ -z "$2" ] || [ "${2#--}" != "$2" ]; then
        refuse "$1 takes a value"
      fi
      case "$1" in
        --region) region=$2 ;;
        --account) account=$2 ;;
        --database) database=$2 ;;
        --workgroup) workgroup=$2 ;;
        --domain) domain=$2 ;;
        --names) names=$2 ;;
        --endpoint) endpoint=$2 ;;
        --attempts) attempts=$2 ;;
        --namespace) namespace=$2 ;;
      esac
      shift 2
      ;;
    *) refuse "unknown option: $1" ;;
  esac
done
for option in region account database workgroup domain names; do
  if [ -z "${!option}" ]; then
    refuse "--$option is required"
  fi
done
case "$names" in
  as-built | glue-arn) ;;
  *) refuse "--names is as-built or glue-arn, not $names" ;;
esac
case "$endpoint" in
  default | http://* | https://*) ;;
  *) refuse "--endpoint is a URL or default, not $endpoint" ;;
esac
case "$attempts" in
  default) ;;
  *[!0-9]* | 0*) refuse "--attempts is a number from 1 or default, not $attempts" ;;
esac
case "$namespace" in
  *[!A-Za-z0-9._-]*) refuse "--namespace is letters, digits, '.', '_' and '-', not $namespace" ;;
esac
if [ "$#" -eq 0 ]; then
  set -- build
fi

# The package python3 imports, whose project is copied to a temporary folder: dbt writes target/ and
# logs/ beside the project it runs, and the archive's folder is not the task's.
package=$(python3 -c 'import app_dbt; print(app_dbt.__file__)')
package=$(dirname "$package")
work=$(mktemp -d)
cp -R "$package/project" "$work/project"

# The wrapper starts `dbt` by name, and package-task removes console scripts: the package carries dbt
# Core's own, used where it sits when the extraction kept its mode, else a copy marked executable.
if [ -x "$package/bin/dbt" ]; then
  bin="$package/bin"
else
  cp -R "$package/bin" "$work/bin"
  chmod +x "$work/bin/dbt"
  bin="$work/bin"
fi
if [ -x "$0" ]; then
  echo "run-dbt.sh: dbt from $bin, this script executable"
else
  echo "run-dbt.sh: dbt from $bin, this script not executable"
fi
echo "run-dbt.sh: $(python3 -c 'import platform, sys; print(sys.executable, platform.python_version(), platform.platform())')"

# The transport's client takes its Region from the environment once endpointOverride replaces its
# region; DO_NOT_TRACK silences dbt's telemetry, each send of which waits up to 5 s; a number of
# attempts reaches every botocore client, the transport's included, which takes no timeout.
export PATH="$bin:$PATH" AWS_DEFAULT_REGION="$region" DO_NOT_TRACK=1
export OPENLINEAGE_NAMESPACE="$namespace"
export APP_DBT_DATABASE="$database" APP_DBT_WORKGROUP="$workgroup"
if [ "$attempts" != default ]; then
  export AWS_MAX_ATTEMPTS="$attempts"
fi

# The product database's location, the profile's s3_data_dir: an Iceberg table's location is the
# adapter's, built from it.
location=$(python3 -c '
import sys

import boto3
from botocore.exceptions import BotoCoreError, ClientError

try:
    database = boto3.client("glue").get_database(Name=sys.argv[1])["Database"]
except (BotoCoreError, ClientError) as error:
    sys.exit("run-dbt.sh: glue:GetDatabase " + sys.argv[1] + ": " + type(error).__name__ + ": " + str(error))
print(database.get("LocationUri", ""))
' "$database")
if [ -z "$location" ]; then
  echo "run-dbt.sh: the database $database has no location in Glue, which the profile's s3_data_dir takes" >&2
  exit 3
fi
case "$location" in
  */) ;;
  *) location="$location/" ;;
esac
export APP_DBT_DATA_DIR="$location"
echo "run-dbt.sh: region $region, account $account, database $database at $location, workgroup $workgroup, domain $domain, names $names, endpoint $endpoint, attempts $attempts, namespace $OPENLINEAGE_NAMESPACE"

# The lineage configuration, in the first place the client looks: the events as the wrapper builds
# them, or each Athena dataset renamed by app_dbt.lineage.GlueTableNames before the post.
export OPENLINEAGE_CONFIG="$work/openlineage.yml"
python3 - "$OPENLINEAGE_CONFIG" "$names" "$domain" "$region" "$account" "$endpoint" <<'PY'
import sys

import yaml

path, names, domain, region, account, endpoint = sys.argv[1:]
transport = dict(type="amazon_datazone_api", domainId=domain, region=region)
if endpoint != "default":
    transport["endpointOverride"] = endpoint
if names == "glue-arn":
    transport = dict(
        type="transform",
        transformer_class="app_dbt.lineage.GlueTableNames",
        transformer_properties=dict(region=region, account_id=account),
        transport=transport,
    )
with open(path, "w", encoding="utf-8") as handle:
    yaml.safe_dump(dict(transport=transport), handle, sort_keys=False)
PY

# The wrapper, which has no __main__, run as a child of a process that reads the peak resident memory
# of the wrapper and of the dbt it starts once both have ended.
cd "$work"
echo "run-dbt.sh: dbt $* in $work/project"
set +e
python3 -c '
import resource
import subprocess
import sys

code = subprocess.call(sys.argv[1:])
peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
if sys.platform == "darwin":
    peak //= 1024
print("run-dbt.sh: peak memory", peak, "kB, exit code", code, flush=True)
sys.exit(code)
' python3 -c 'import sys; from openlineage.dbt import main; sys.exit(main())' \
  "$@" --project-dir "$work/project" --profiles-dir "$work/project"
code=$?
set -e
exit "$code"
