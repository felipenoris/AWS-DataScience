# Runbook — the buildbox (retired)

The buildbox, the `[E]` `amd64` host that built the images by hand (`production/buildbox/`, six releases
from `default-v0.1.0` to `default-v0.5.0`), was retired at
[Stage 7 step 6.5](../stages/stage-07-gitlab-runners-ecr.md) on 2026-10-12. Its slice, its script and
this runbook's procedures are gone; this page stays so that the stage logs which link here still resolve.

| What this runbook held | Where it is now |
|---|---|
| Building the images, and what to check before a build | [`gitlab/awsds/dev-env/README.md`](../../../gitlab/awsds/dev-env/README.md), the build runner's pipeline |
| The release ledger (§P): every tag, its date, what it changed, its sizes | [`gitlab/awsds/dev-env/README.md`](../../../gitlab/awsds/dev-env/README.md) §*The releases* |
| The build host's network and its proxy layers | the build runner, [`gitlab.md`](gitlab.md) §K and [`docs/NETWORK.md`](../../NETWORK.md) |
| The push and its identity | the runner's role through the ECR credential helper ([`gitlab.md`](gitlab.md) §K) |

The page as it stood before the retirement is in the repository's history: `git show a3f698b:docs/plan/runbooks/buildbox.md`.
