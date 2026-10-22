# <env>/app/app-etl/ - the application's structure in a deployment target (Stage 8 steps 3.2 and 3.6,
# D41 item 9): its Glue job, awsds-<env>-app-etl (Stage 10 decision 20 (a)), which the workflow's
# transform task starts by name. Layer [E]: the Staging leg's `make down` destroys it, and `make up`
# never applies it (layers.py refusal 7); the pipeline applies it with the release it promotes.
#
# The job runs the release's script, which the release job copied under the release's prefix of the
# outputs bucket (Stage 10 decisions 1 and 12), as Stage 9's [P] awsds-<env>-job-exec, on the
# account's Glue connection, whose job group it carries (Stage 9 decision 12 (a)): the slice declares no
# network of its own. Its logs go to Glue's default groups, which sagemaker/ creates. The shape is the
# Glue task's create_job_kwargs in examples/app-etl/workflows/app-etl.yaml, where the operator creates
# the job in dev and test; the render drops those keys here (Stage 10 decision 6).
#
# The same file in staging/app/app-etl/ and production/app/app-etl/, byte for byte
# (./scripts/check-copies.py); release.tf is each account's own.

locals {
  name = "awsds-${var.env}-app-etl"

  release_prefix = var.release == null ? null : "s3://${data.terraform_remote_state.data.outputs.outputs_bucket_name}/applications/app-etl/${var.release.tag}"
}

resource "aws_glue_job" "this" {
  # checkov:skip=CKV_AWS_195:no security configuration - its CloudWatch encryption renames the job's log groups away from the ones sagemaker/ creates and the job role names, the outputs bucket's default encryption under the data key covers the job's writes, and the job keeps no bookmark
  count = var.release == null ? 0 : 1

  name              = local.name
  description       = "app-etl's Glue job (Stage 8 step 3.2): the release's glue/transform.py, started by the workflow awsds-${var.env}-wf-app-etl"
  role_arn          = data.terraform_remote_state.sagemaker.outputs.job_role_arn
  glue_version      = "6.0"
  worker_type       = "G.1X"
  number_of_workers = 2
  timeout           = 50
  connections       = [data.terraform_remote_state.sagemaker.outputs.glue_connection_name]

  command {
    name            = "glueetl"
    script_location = "${local.release_prefix}/glue/transform.py"
    python_version  = "3"
  }

  execution_property {
    max_concurrent_runs = 1
  }

  tags = {
    Name = local.name
  }
}
