
# Proxy Config on SageMaker

## How to produce

Read as output of terraform endpoints:

```
cd terraform-live/sandbox/egress && terraform output -raw no_proxy
```

On JupyterLab terminal:

```
export http_proxy=http://proxy.awsds.internal:3128 https_proxy=$http_proxy HTTP_PROXY=$http_proxy HTTPS_PROXY=$http_proxy no_proxy='<cole a saída acima>' NO_PROXY=$no_proxy && curl -s -o /dev/null -w '%{http_code}\n' --max-time 20 https://pypi.org/
```

## Latest reading

```
export NO_PROXY='.awsds-pages.internal,.awsds.internal,127.0.0.1,169.254.169.254,169.254.170.2,api.ecr.us-west-2.amazonaws.com,api.sagemaker.us-west-2.amazonaws.com,athena.us-west-2.amazonaws.com,datazone.us-west-2.amazonaws.com,dkr.ecr.us-west-2.amazonaws.com,dynamodb.dualstack.us-west-2.amazonaws.com,dynamodb.us-west-2.amazonaws.com,ec2.us-west-2.amazonaws.com,ec2messages.us-west-2.amazonaws.com,glue.us-west-2.amazonaws.com,kms.us-west-2.amazonaws.com,lakeformation.us-west-2.amazonaws.com,localhost,logs.us-west-2.amazonaws.com,runtime.sagemaker.us-west-2.amazonaws.com,s3.dualstack.us-west-2.amazonaws.com,s3.us-west-2.amazonaws.com,s3tables.us-west-2.amazonaws.com,secretsmanager.us-west-2.amazonaws.com,ssm.us-west-2.amazonaws.com,ssmmessages.us-west-2.amazonaws.com,sts.us-west-2.amazonaws.com,studio.us-west-2.sagemaker.aws'

export no_proxy="$NO_PROXY" http_proxy=http://proxy.awsds.internal:3128 https_proxy=http://proxy.awsds.internal:3128 HTTP_PROXY=http://proxy.awsds.internal:3128 HTTPS_PROXY=http://proxy.awsds.internal:3128
```

## `apt` — the variables do not survive `sudo`

Measured 2026-09-08. `sudo` resets the environment (`env_reset`) and `http_proxy` is not in its
`env_keep`, so `apt` runs with a clean environment, resolves the destination itself and is refused by the
Sandbox DNS Firewall — `Could not resolve 'archive.ubuntu.com'`, on a name that **is** on the proxy's
allow-list. Exporting the variables first changes nothing, and that is the tell.

Use `apt`'s own option, which needs neither the environment nor a sudoers change:

```
sudo apt -o Acquire::http::Proxy="http://proxy.awsds.internal:3128" -o Acquire::https::Proxy="http://proxy.awsds.internal:3128" update
```

The durable form is in the house image, not in a shell: `/etc/apt/apt.conf.d/01proxy` carrying those two
`Acquire::` lines, plus a sudoers `env_keep` for the six proxy variables so a person's exports survive
`sudo` for everything that is not `apt`. Both belong to Stage 6d step 2.2.

## Code Editor — the extension gallery has no proxy at all

Measured 2026-09-08. A Code Editor space fails to update **AWS's own** `aws-toolkit-vscode` and
`amazon-q-vscode` at every start, with `getaddrinfo ENOTFOUND open-vsx.org`. That is a **resolution**
failure, so the VS Code server never had proxy variables — the allow-list was never consulted.
`open-vsx.org` is now on the compute plane (committed, unapplied); the delivery mechanism is the open
half, and both are Stage 6d **step 8**.
