# Objectives — what this project must achieve

*The requirements brief, in the user's own words. **Moved here from `CLAUDE.md` on 2026-08-15**, unchanged,
when that file went over its 20 KB budget; it is the specification every stage is measured against, so it
is copied nowhere and summarised nowhere — `CLAUDE.md` points here instead.*

---

The objective of this project is to create a Data Science environment based on AWS cloud infrastructure, using my personal AWS account.

The goal is to achieve the following:

- All user access to the cloud infrastructure will be performed through a VPN.

- Once connected to the VPN, all of the client's internet access will go through an egress inside the
  AWS cloud *(added 2026-08-25)*. This has two implications, both tied to the DLP objective (Stage 11):
  (1) the client can reach the organization's cloud infrastructure only while connected to the VPN;
  (2) all internet access will be monitored — there will be an HTTP/HTTPS proxy between the
  VPN-connected client and the cloud's internet egress. Once on the VPN, the user can therefore use the
  browser to reach the internet, which includes the SageMaker portal and the public links that are usage
  requirements of SageMaker (the network-isolation guide's public-internet-access section). In the
  real-world institution this models, only institution-owned laptops can connect to the VPN, and those
  laptops carry their own endpoint DLP (a Microsoft 365 service) — so requiring the VPN closes the
  circuit: nothing extracted through SageMaker, even by downloading files to the laptop, leaves the
  institution unmonitored.

- Use SageMaker Unified Studio as a development tool for Data Scientists.

- The main features Data Scientists can use inside SageMaker Unified Studio to develop data-science products are:

  - the use of Jupyter notebooks built in SageMaker Unified Studio: users can instantiate as many Jupyter notebook instances as they like, each one on a selected compute and dev-env image.
  - the user of vscode instances built in SageMaker Unified Studio: users can instantiate as many vscode web instances they wish, with possibility of remote connecting their local computer vscode to a remote session.
  - the use of data catalog and explorer, issuing SQL statements, built in SageMaker Unified Studio.
  - use of S3 buckets for storage, built in SageMaker Unified Studio user interface.
  - connect to user's `sso-group` S3 bucket using SageMaker to read-write data to group's `sandbox-lake`.
  - use of sagemaker's workflows and Visual ETL feature built in SageMaker Unified Studio.
  - use of IA models built in SageMaker Unified Studio

- The data scientist can promote Artifacts built in SageMaker (dev-env, ML models, workflows) to production (Sandbox -> Staging -> Production), making use of CI/CD pipelines (see below).

- Protect data against leakage (DLP), mainly targeting SageMaker. There is no single AWS product that does
  this, so the requirement is broken into the four problems it has to solve:

	- sensitive-data discovery and classification: know which sensitive data exists and where it is stored.
	- fine-grained access control: restrict who can read which database, table, column and row.
	- egress control: restrict where data can be sent to from the development environment.
	- exfiltration detection: detect and alert on abnormal data access or data movement.

- SageMaker should have access to the internet. We'll explore implementing some restrictions, keeping the possibility of software updates, installing packages, and accessing a few websites.

  *Clarified 2026-08-25 — scope and mechanism:* the restriction is on the **SageMaker-managed compute**,
  never on the user's (client's) machine — the client, on the VPN, has monitored internet through the
  institutional proxy (see the VPN bullet above). The compute's restriction is stricter: under D5's
  design (A) only a few sites are allowed, for downloading programming-language packages and perhaps
  data from providers associated with data-science work; under design (B) the compute's internet access
  is fully blocked, packages arriving through the image and CodeArtifact as D5 already describes. The
  difference between (B) and (A) is small: with an internet whitelist, (B) is the empty list and (A) a
  short one. The SageMaker compute also has access to "intranet" resources, which includes this lab's
  GitLab instance. And the whole cloud will have a **single internet egress point and a single
  HTTP/HTTPS proxy**: even a site on SageMaker's whitelist is reached through that proxy — two filters,
  the institutional proxy's and SageMaker's stricter one on top.

- Use GitLab hosted on AWS for source-code control, accessible only through intranet (VPN), not facing public internet.

- Use GitLab Pages to host docs, accessible only through intranet (VPN), not facing public internet.

- Use GitLab CI/CD to automate tests, docs and deployment.

- Use three kinds of CI/CD pipelines:

	- pipeline to build a development environment: this will be the Docker container (or image) used by developers on SageMaker.
	- pipeline to build an application: this should build a Docker image of the app.
	- pipeline to deploy an application into the production environment.

- Explore the possibility of deploying a workflow developed in SageMaker (Airflow/MWAA) to production.

- Data-science assets and databases should not face the public internet. Later in the project we'll experiment with setting up a web server facing the public internet, accessing a backend or database protected in the private subnet.

- Let's avoid using IAM Users, in favor of assuming IAM Roles temporarily.

- Use AWS CloudWatch to monitor the cloud infrastructure.

- Use AWS Organizations + Control Tower to set up account permissions.

- Use AWS Lake Formation to share data cross-account.

- Use AWS Glue Data Catalog with data stored on S3 buckets, using ICEBERG format, as Data Warehouse.

- Use Amazon ECR as container registry.

## How this will be done

We will start from scratch: the starting point is a root AWS account created manually.

The project will be implemented incrementally.

I'll ask Claude to plan the next step and Claude will guide me on each step until we reach the project goals.

The application repository template (`app-etl`) is a layout convention, and lives with the others:
[`docs/plan/conventions.md`](conventions.md), "Application repository layout".

---

*Plan core: [GENERAL_PLAN.md](../GENERAL_PLAN.md) · Working rules: [`CLAUDE.md`](../../CLAUDE.md) · Route: [`docs/plan/stages/INDEX.md`](stages/INDEX.md)*
