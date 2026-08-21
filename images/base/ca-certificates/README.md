# The CA-install layer's source directory — empty on purpose

`images/base/Dockerfile` copies this directory into `/usr/local/share/ca-certificates/awsds/`
and runs `update-ca-certificates`. **Today it contains no certificate**, and the build asserts
that: `CA_ROOTS_EXPECTED` defaults to `0`, and a `.crt` appearing here without the build
argument being raised fails the build rather than being silently trusted.

**Why it is empty** — D36 §3, amended 2026-08-21. The internal CA root moved back to
[Stage 7](../../../docs/plan/stages/stage-07-gitlab-runners-ecr.md) with the leaf certificates,
because the only names the root lets a container trust — `gitlab.prod.internal`,
`*.pages.internal` — do not exist while Stage 6 runs. Every endpoint Stage 6 touches is an AWS
public endpoint with a publicly-signed certificate.

**Who fills it** — Stage 7 step 2.6, from `production/pki/`'s output (INT-19), never a pasted
PEM. One file, `.crt` extension, then rebuild with `--build-arg CA_ROOTS_EXPECTED=1`.

This file is not a certificate, so `update-ca-certificates` ignores it; it exists so the
directory survives in git and the `COPY` has something to copy.
