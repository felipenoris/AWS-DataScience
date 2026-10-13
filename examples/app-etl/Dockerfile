# app-etl's image (Stage 8 step 2.2): the application image, and the job image a SageMaker processing job
# runs it in (Stage 10 decision 7).
#
# FROM base by digest, never FROM dev-env and never a base of its own: base is the common ancestor the
# notebook image also descends from, so the code runs on the interpreter and the OS it was written against
# (D17). The digest is default-v0.6.0, Sandbox's image version 6; REGISTRY is the build runner's
# ECR_REGISTRY, so the account is no literal here.
#
# Two targets. `app` is what the pipeline pushes. `smoke` runs the job's command the way a processing job
# does, as the image's user with networking off, on an output directory created owned by root with mode
# 755, which is how the platform creates the processing mounts (6i); the command opens with the job's
# `sudo -n chown`, which needs the passwordless sudo the SageMaker Distribution grants (decision 8).

ARG REGISTRY
FROM ${REGISTRY}/awsds-prod-ecr-base@sha256:94359041f65b8bfada3ec1603937dadd49055854c034910f20d8be4a53341975 AS app

# The project and its locked dependencies, in a virtual environment of its own on base's interpreter. base
# carries no environment for an application (only dev-env builds one) and refuses to download a Python
# (UV_PYTHON_DOWNLOADS=never), so the interpreter is named. The environment is root's and read-only to the
# job; the source tree is removed once the wheel is installed, and no uv cache enters a layer.
USER root
ENV APP_ETL_VENV=/opt/app-etl/venv
COPY pyproject.toml uv.lock README.md /tmp/app-etl/
COPY src/ /tmp/app-etl/src/
RUN set -eu; \
    cd /tmp/app-etl; \
    UV_PROJECT_ENVIRONMENT="${APP_ETL_VENV}" UV_NO_CACHE=1 \
      uv sync --locked --no-dev --no-editable --python /opt/conda/bin/python3.12; \
    "${APP_ETL_VENV}/bin/python" -c 'import app_etl, pyarrow, sys; print("app-etl", app_etl.__version__, "pyarrow", pyarrow.__version__, "python", sys.version.split()[0])'; \
    cd /; rm -rf /tmp/app-etl
ENV PATH="${APP_ETL_VENV}/bin:${PATH}"

# The synthetic sample, read by a job that has no input of its own: Sandbox's engineering run (step 2.4)
# writes Sandbox data from it without a person writing an object under the account's data key (D31).
COPY samples/ /opt/app-etl/samples/

LABEL org.opencontainers.image.title="app-etl" \
      org.opencontainers.image.description="Every CSV in a directory becomes a Parquet table and a JSON summary" \
      org.opencontainers.image.base.name="awsds-prod-ecr-base:default-v0.6.0"

USER ${MAMBA_USER}

FROM app AS smoke
USER root
RUN mkdir -p /opt/ml/processing/input /opt/ml/processing/output \
 && chmod 0755 /opt/ml/processing/output
COPY samples/ /opt/ml/processing/input/
USER ${MAMBA_USER}
RUN --network=none set -eu; \
    echo "uid $(id -u), output owned $(stat -c '%u:%g %a' /opt/ml/processing/output)"; \
    sudo -n chown "$(id -u)" /opt/ml/processing/output; \
    python -m app_etl --input /opt/ml/processing/input --output /opt/ml/processing/output; \
    test -s /opt/ml/processing/output/trades.parquet; \
    test -s /opt/ml/processing/output/trades.summary.json; \
    echo "smoke: passed"
