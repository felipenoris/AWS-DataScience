# The CA-install layer's source directory

`base/Dockerfile` copies this directory into `/usr/local/share/ca-certificates/awsds/`
and runs `update-ca-certificates`. It holds one certificate, `awsds-root.crt`, the internal CA's
root (`production/pki/`, D36), and the build asserts the count: `CA_ROOTS_EXPECTED` is `1`, and a
file lost from here or a second one appearing fails the build rather than changing what the image
trusts in silence.

**Where the file comes from** — Stage 7 step 2.6 (2026-10-12), read from the published parameter
`/datascience/prod/pki/ca-root-pem` with `aws ssm get-parameter`, never pasted (INT-19). Its SHA256
fingerprint is in [the Stage 7 log](https://github.com/felipenoris/AWS-DataScience/blob/main/docs/log/log-stage-07-gitlab-runners-ecr.md); a root
rotation (D36 §6) replaces the file from the same parameter and rebuilds both images.

**What the file lets a container reach** — `gitlab.awsds.internal` and `*.awsds-pages.internal`, the
two names the root certifies: a `git clone` from a notebook (INT-09) and nothing else. Every AWS
endpoint the image touches carries a public certificate and needs nothing from here.

The layer stood empty from Stage 6 until this step (D36 §3, amended 2026-08-21), because the names it
certifies did not exist before Stage 7.
