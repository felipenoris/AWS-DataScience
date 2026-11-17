# Log — Stage 21 — Redshift tables and S3 objects as data products in SageMaker Unified Studio

*Written cooperatively. Every entry names whose hand performed the act; a measurement the user pasted
stays verbatim. The stage file is
[`docs/plan/stages/stage-21-redshift-s3-data-products.md`](../plan/stages/stage-21-redshift-s3-data-products.md).
Account ids are replaced by the account's name in angle brackets.*

---

## 2026-11-17 — the stage written from AWS's pages and the repository, with no AWS call

*Claude's sitting in a cloud session, no AWS call: AWS's pages read through a fetcher, recorded in
[`REFERENCES.md`](../REFERENCES.md) the same sitting.*

- **[user] The request**, in a cloud session's thread at 19:12 and 19:14 UTC, quoted whole in the stage
  file's "The premises": how to structure SageMaker Unified Studio, by AWS's recommendation, for publishing
  and sharing data products between teams; how Redshift meets the Glue Data Catalog and the SageMaker
  Catalog with its lineage; whether a Redshift table can be a data product by the standard path; which
  datasets the Glue Data Catalog holds; whether reading Redshift data requires a given compute, where a
  Parquet file on S3 leaves the engine free; whether the Glue Data Catalog holds images; and *"Se para
  responder estas perguntas for necessário exercitar no lab, planeje um novo stage do plano para isso."*
  The same thread had answered from 17:54 UTC why the portal's *Create table → Redshift table* failed in
  the institution's environment with *"Cannot find default IAM role on this cluster"* (code 30001, `IAM
  role ARN "none"`): the namespace holds no default IAM role, and the user changed nothing there (18:54
  UTC). The session held no AWS credential and made no apply and no portal act; it read the repository at
  `main` `7816fbe`, then `922c4d0`.
- **[Claude] The review of the repository**, recorded in the stage file's "The plan and the estate against
  the premises" and "0. What is already measured": D12, D13, D26 and D40; 5b, 6f and 6h; Stage 9 decision 5
  and its 9.5a; Stage 19's 0.6, decision 9 and verifications v to ix; `GOVERNANCE.md`, `SMUS.md`,
  `catalog.md`, `redshift-connection.md` and `promotion.md` §N.6; `./aws/warehouse.py` and
  `./aws/catalog.py`. The readings the design turns on:
  - no Redshift subscription target in any environment and no federated catalog in any account (Stage 19
    0.6, 2026-10-28);
  - the Sandbox namespace's default role, `awsds-sandbox-warehouse-exec`, holds no policy (5b decision 5),
    so the portal's *Create table → Redshift table* is expected to fail here on S3, not on a missing default
    role;
  - `test-experimentation` is in no map and 6h decision 8 is untaken; its (a), the wide tag, gives every
    project role the workgroup from a notebook or the Data API (6h, simulated 2026-10-18);
  - Stage 9 decision 5 took the datashare in Production on 2026-10-22 against the managed cluster data lake
    access creates, and 9.5a's reading is owed only if the federated catalog comes back;
  - the account's S3 Access Grants instance holds one location per project and no grant
    (`SMUS.md`, 2026-08-23);
  - the connection's `lineageSync` failed on every run read (`EXC-17`).
- **[Claude] AWS's pages, read 2026-11-17**, recorded in `REFERENCES.md` (two entries under "SageMaker and
  shared storage", one under "Data platform") and quoted in the stage file's "The user's questions,
  answered": SageMaker Unified Studio's pages on managed assets, the fulfilment of a Redshift and of a Glue
  asset, the Redshift and Glue data sources, data products, the S3 Object Collection and S3 Access Grants, a
  project's Redshift compute, Redshift lineage and the domain's organization; DataZone's
  `CreateSubscriptionTarget`; Lake Formation's and Redshift's pages on the federated catalog, its
  prerequisites and limits, and the RMS catalog; Glue's pages on tables, classifiers, formats, views and the
  Iceberg REST catalog; Athena's catalog registrations; Glue's, Redshift's and the lakehouse's pricing; S3
  Metadata.
- **[Claude] What the pages leave open or contradict**, each a step of the stage:
  - cross-Region subscriptions: the Glue and Redshift asset pages say none is supported, and the unmanaged
    asset's page supports Glue tables and views and Redshift tables and views across standard Regions with
    the blueprint enabled in both; written into `catalog.md` §S;
  - the compute behind data lake access: *"a managed Amazon Redshift cluster"* on the federated catalog's
    page, *"an Amazon Redshift managed serverless-workgroup"* on the RMS catalog's, *"a service-managed
    Amazon Redshift Serverless workgroup"* on Glue's pricing page; no page names its account or base
    capacity (decision 3, 4.5);
  - a Redshift subscription target for a project admitted by hand: no page, and `CreateSubscriptionTarget`'s
    reference names no Redshift type or form (decision 1, 2.4);
  - a Glue data source over a federated catalog: the catalog can be typed, and no page says its tables
    import, nor as which type (4.4);
  - an S3 Object Collection's grantee and how a subscriber reads it: no page (5.4, 5.5);
  - pages that answered nothing: the portal's page on creating a table, an empty stub in English and
    Japanese, with the guide's PDF failing; Lake Formation's page on accessing catalogs, a client error as
    `.md` and the guide's title alone as `.html`; What's New's search, which renders by script.
- **[Claude] 1.4's generator, run on the session's host** with Python's standard library: 20 PNG files of
  64 × 64, 177 to 180 bytes each and 3,580 in all, every chunk's CRC and each image's decompressed size
  checked, `file` reading the first as *"PNG image data, 64 x 64, 8-bit/color RGB, non-interlaced"*; 13
  labelled `quente` and 7 `fria`.
- **[Claude] The stage written**, decisions 1 to 3 put to the user and none taken; the indexes,
  `GENERAL_PLAN.md`'s route, `CLAUDE.md`'s Current position, the waiting list, `catalog.md` §S and
  `promotion.md` §N.6 item 9 amended in the same pull request.
