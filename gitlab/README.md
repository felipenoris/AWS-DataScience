# `gitlab/` — copies of the projects the private GitLab holds

The image recipes live in the private GitLab since 2026-10-14 ([Stage 8](../docs/plan/stages/stage-08-cicd-pipelines.md)
decision 16), and GitLab is their source of truth. This folder keeps a copy of each project's last commit,
so the recipe can be read, reviewed and checked from this repository without the VPN.

| Copy | GitLab project | What it holds |
|---|---|---|
| [`awsds/dev-env/`](awsds/dev-env/README.md) | `awsds/dev-env` | the house image's recipe: `base`, `dev-env`, the smoke test and their pipeline |
| [`awsds/deploy-image/`](awsds/deploy-image/README.md) | `awsds/deploy-image` | the deploy image's recipe and its pipeline |

`mirror.json` names the commit each copy holds; the script that writes the copy writes it, at its first run.

## The two scripts

| Script | What it does | Needs |
|---|---|---|
| [`scripts/gitlab-mirror.py`](../scripts/gitlab-mirror.py) | replaces each copy with its project's last commit on `main`, reporting every file added, removed or changed; `--dry-run` reports and writes nothing | the VPN tunnel, GitLab up, and git's own credential for `gitlab.awsds.internal` |
| [`scripts/check-gitlab-mirror.py`](../scripts/check-gitlab-mirror.py) | reads `awsds/dev-env`'s copy against the estate: the `NO_PROXY` literal against `sandbox/egress`'s `no_proxy_all_groups`, and the Bedrock settings against the SCP and `sandbox/bedrock/`'s grant; a failure names the file to change in GitLab | an SSO session as the infrastructure user; `--plan` reads the list from a plan of `sandbox/egress` when that slice is down |

## Changing a recipe

1. Run `./scripts/check-gitlab-mirror.py` and read section *What to change in GitLab*.
2. Make the change in GitLab, by a merge request on the project, and push it.
3. Run `./scripts/gitlab-mirror.py`, then commit the copy and `mirror.json` here.

An edit made under this folder first is a proposal: it is true once GitLab holds it and
`gitlab-mirror.py` reports the copy unchanged. Uncommitted changes under a copy stop that script before
it writes anything. pre-commit's fixers skip this folder, since a fix made here would make the copy differ
from GitLab; its checks for keys, account ids and e-mail addresses still read it.
