# app-ml's image (Stage 17 step 9.2): the job image both prepare tasks run in, app-etl's Dockerfile with
# app-ml's command.
#
# FROM base by digest, never FROM dev-env and never a base of its own: base is the common ancestor the
# notebook image also descends from, so the code runs on the interpreter and the OS it was written against
# (D17). The digest is default-v0.6.0, Sandbox's image version 6; REGISTRY is the build runner's
# ECR_REGISTRY, so the account is no literal here.
#
# The image carries the lock's runtime set and not the code: the code is the job's input, `src/` under the
# project's shared prefix, mounted at /opt/ml/processing/code (Stage 10 decision 7, D41 item 7), so a change
# to the code is a deploy and not a build. app-ml's runtime set is empty, so the environment holds base's
# interpreter alone. The XGBoost image that trains and serves the model is AWS's, by digest
# (TRAINING_IMAGE_URI), and never this one. Two targets. `app` is what the pipeline pushes. `smoke` runs
# both modes of the job's command the way a processing job does, as the image's user with networking off,
# the code mounted read-only from `src/`, on an output directory created owned by root with mode 755, which
# is how the platform creates the processing mounts (6i); the command opens with the job's `sudo -n chown`,
# which needs the passwordless sudo the SageMaker Distribution grants (Stage 10 decision 8).

ARG REGISTRY
FROM ${REGISTRY}/awsds-prod-ecr-base@sha256:94359041f65b8bfada3ec1603937dadd49055854c034910f20d8be4a53341975 AS app

# The locked runtime set, in a virtual environment of its own on base's interpreter, so `python` is
# base's CPython 3.12 and a dependency the lock gains reaches the job without a change here. base refuses
# to download a Python (UV_PYTHON_DOWNLOADS=never), so the interpreter is named. The environment is
# root's and read-only to the job; the project files leave once it exists, and no uv cache enters a layer.
USER root
ENV APP_ML_VENV=/opt/app-ml/venv
COPY pyproject.toml uv.lock README.md /tmp/app-ml/
RUN set -eu; \
    cd /tmp/app-ml; \
    UV_PROJECT_ENVIRONMENT="${APP_ML_VENV}" UV_NO_CACHE=1 \
      uv sync --locked --no-dev --no-install-project --python /opt/conda/bin/python3.12; \
    "${APP_ML_VENV}/bin/python" -c 'import sys; print("python", sys.version.split()[0], sys.executable)'; \
    cd /; rm -rf /tmp/app-ml
ENV PATH="${APP_ML_VENV}/bin:${PATH}"

LABEL org.opencontainers.image.title="app-ml" \
      org.opencontainers.image.description="A churn table becomes XGBoost's training and scoring sets" \
      org.opencontainers.image.base.name="awsds-prod-ecr-base:default-v0.6.0"

USER ${MAMBA_USER}

FROM app AS smoke
USER root
RUN mkdir -p /opt/ml/processing/input /opt/ml/processing/output \
 && chmod 0755 /opt/ml/processing/output
COPY samples/ /opt/ml/processing/input/
USER ${MAMBA_USER}
RUN --network=none --mount=type=bind,source=src,target=/opt/ml/processing/code,readonly set -eu; \
    echo "uid $(id -u), output owned $(stat -c '%u:%g %a' /opt/ml/processing/output)"; \
    sudo -n chown "$(id -u)" /opt/ml/processing/output; \
    cd /opt/ml/processing/code; \
    python -m app_ml.prepare train --input /opt/ml/processing/input --output /opt/ml/processing/output/train; \
    python -m app_ml.prepare score --input /opt/ml/processing/input --output /opt/ml/processing/output/score; \
    test -s /opt/ml/processing/output/train/train/train.csv; \
    test -s /opt/ml/processing/output/train/validation/validation.csv; \
    test -s /opt/ml/processing/output/score/batch/batch.csv; \
    test -s /opt/ml/processing/output/score/labels/labels.csv; \
    echo "smoke: passed"
