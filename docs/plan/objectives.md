# Objectives — what this project must achieve

*The requirements brief, in the user's own words. **Moved here from `CLAUDE.md` on 2026-08-15**, unchanged,
when that file went over its 20 KB budget; it is the specification every stage is measured against, so it
is copied nowhere and summarised nowhere — `CLAUDE.md` points here instead.*

---

The objective of this project is to create a Data Science environment based on AWS cloud infrastructure, using my personal AWS account.

The goal is to achieve the following:

- The VPN is a prerequisite only for reaching resources on the private network by IP address. The user
  connects to it to navigate inside the private network, its IP addresses and its DNS, and to reach the
  resources that are not exposed to the public internet. Being connected to the VPN is not required to
  access SageMaker Unified Studio or the AWS console.

- An IAM identity is granted only to users who sign in from laptops monitored by the institution, which
  carry their own DLP implemented by Microsoft 365.

- Two types of VPN access *(the second added 2026-09-08)*:

  - **monitored**: once connected to the VPN, all of the client's internet access will go through an
    egress inside the AWS cloud *(added 2026-08-25)*, and all of it will be monitored: there will be an
    HTTP/HTTPS proxy between the VPN-connected client and the cloud's internet egress. Once on the VPN,
    the user can therefore use the browser to reach the internet, which includes the SageMaker portal and
    the public links that are usage requirements of SageMaker (the network-isolation guide's
    public-internet-access section). In the real-world institution this models, only institution-owned
    laptops can connect to the VPN, and those laptops carry their own endpoint DLP (a Microsoft 365
    service).

  - **split-tunnel**: a client connected in this profile reaches the private address space through the
    tunnel, but its internet access is routed by the client through its own uplink — without crossing
    the private network, and unchecked by the private proxy. As a consequence the client needs no proxy
    configuration for its internet access, its calls to AWS included. Nothing on the cloud side changes
    between the two profiles: the difference is one line of the client's own configuration, which in the
    institution would be fixed by MDM. This profile is used to proceed with the plan's implementation;
    the monitored profile is the institution's, used whenever an aspect that models the institution is
    being tested.

- Use SageMaker Unified Studio as a development tool for Data Scientists.

- The main features Data Scientists can use inside SageMaker Unified Studio to develop data-science products are:

  - the use of Jupyter notebooks built in SageMaker Unified Studio: users can instantiate as many Jupyter notebook instances as they like, each one on a selected compute and dev-env image.
  - the user of vscode instances built in SageMaker Unified Studio: users can instantiate as many vscode web instances they wish, with possibility of remote connecting their local computer vscode to a remote session.
  - the use of data catalog and explorer, issuing SQL statements, built in SageMaker Unified Studio.
  - use of S3 buckets for storage, built in SageMaker Unified Studio user interface.
  - connect to user's `sso-group` S3 bucket using SageMaker to read-write data to group's `sandbox-lake`.
  - connect a SageMaker project to a Redshift database through a connection, and read and write it from
    the project's notebooks and from its Data page.
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
  never on the user's (client's) machine — a client on the monitored VPN profile has monitored internet
  through the institutional proxy (see the VPN bullets above). The compute's restriction is stricter: under D5's
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

  *Revised 2026-09-20 — a second engine, not a replacement:* the Glue Data Catalog over Iceberg on S3 stays
  the data warehouse of record, and **Amazon Redshift Serverless is a second possible engine beside it**. A
  query engine is a choice per workload, not per estate: Athena over the governed lake remains the default,
  and Redshift is there for what it serves better. Nothing moves out of the lake to make room for it, and
  the governance model does not fork — a governed Redshift database is governed by Lake Formation like a
  lake table is.

- Use Amazon Redshift Serverless as a second query engine, at the smallest capacity the service offers,
  with two types of database:

  - **governed databases**: written by workloads of the production environment, and by nothing else.
  - **sandbox databases**: written by the SageMaker project profiles, with this access granted per database
    x project.

  It is one Redshift environment from a data scientist's point of view. Where its databases physically live
  is an implementation matter, provided a governed database is never written from the sandbox.

  *Clarified 2026-09-20 — the controls do not change:* Redshift is **one more execution environment**, not a
  new class of reader and not a second governance model. A governed Redshift database is read by whoever the
  governed data's grant register already admits, through Lake Formation, exactly as a governed lake table is;
  it is written only by the production workloads. The per database x project grant is the sandbox databases'
  rule, and it is the only new rule here.

  *Clarified 2026-09-20 — the sandbox databases bypass the catalog:* for a sandbox database the catalog and
  Lake Formation are **not** in the path. Access is granted **directly to the project role**, by whichever
  mechanism is simplest to configure, and **a data scientist who is a member of the project creates tables
  freely inside that schema** in Redshift. The asymmetry is deliberate and it is the same one the
  `sandbox-lake` already has: governed data is governed, and a project's working data is the project's.

  *Clarified 2026-09-20 — what a "database" means here, and who shares one:* in Redshift, **a schema is a
  database** in the sense this brief uses the word. So the unit that is granted per base x project is a
  **schema**, and:

  - **one sandbox schema can be shared with more than one SageMaker project** — access is given to a project
    profile, and several may hold it on the same schema.
  - **a schema's name is chosen when the schema is created, after the theme of the data it will hold**, and it
    bears no necessary relation to any SageMaker project.
  - **the disk quota on a sandbox schema is 1 TB.**

- Use Amazon ECR as container registry.

## How this will be done

We will start from scratch: the starting point is a root AWS account created manually.

The project will be implemented incrementally.

I'll ask Claude to plan the next step and Claude will guide me on each step until we reach the project goals.

The application repository template (`app-etl`) is a layout convention, and lives with the others:
[`docs/plan/conventions.md`](conventions.md), "Application repository layout".

---

*Plan core: [GENERAL_PLAN.md](../GENERAL_PLAN.md) · Working rules: [`CLAUDE.md`](../../CLAUDE.md) · Route: [`docs/plan/stages/INDEX.md`](stages/INDEX.md)*
