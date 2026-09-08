
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
