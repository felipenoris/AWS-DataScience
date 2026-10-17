# Log — Stage 17 — Machine learning in a Sandbox project

*Written cooperatively. Every entry names whose hand performed the act; a measurement the user pasted
stays verbatim. The stage file is
[`docs/plan/stages/stage-17-sandbox-machine-learning.md`](../plan/stages/stage-17-sandbox-machine-learning.md).
Account ids are replaced by the account's name in angle brackets.*

---

## 2026-10-17 — pass 0 written in a cloud session, nothing run

- **[user] Pass 0 is written from a cloud session.** In a thread of the Claude project, at 19:22 UTC, the
  user answered the card *"Qual passo do AWS-DataScience tocamos agora, em paralelo à medição em
  Staging?"* with *"Stage 17, passo 0"*, whose consequence read *"Escrevo aqui o instrumento
  (sandbox-ml.py) e os exemplos do passo, e você roda as leituras no laptop. Não toca em Staging nem na
  SCP."* The cloud session holds no AWS credential: no `aws` call ran in it, so nothing below is a
  measurement of AWS.
- **[Claude] 0.1, `./aws/sandbox-ml.py`, written and not run.** `ML-1`..`ML-9` as the stage file lists
  them; its contracts and the halves it cannot close are in [`aws/INDEX.md`](../../aws/INDEX.md),
  "`sandbox-ml.py`, written for Stage 17". Its parsing and its verdicts were exercised against a
  fabricated `aws` executable. Its first run on the laptop is 0.1's before, and carries 0.2 (`ML-7`), 0.5
  (`ML-9`) and 0.8 (`ML-1`).
- **[Claude] 0.6, [`examples/sandbox-ml/`](../../examples/sandbox-ml/README.md), written and not run
  against AWS**: a script per step for a terminal of a space, the pipeline definition with every
  account-scoped value a placeholder, and the README with the values, the commands of a sitting and what
  the first run decides. They were written against the house environment's lock
  (`gitlab/awsds/dev-env/dev-env/python/uv.lock`): `boto3` 1.43.92, `mlflow` 3.16.0, `sagemaker-mlflow`
  0.5.0, `sagemaker` 3.21.0, `pandas` 2.3.3, `xgboost-cpu` 3.3.0, Python 3.12. Step 0.3 reads what the
  space holds, and a script that disagrees changes before it runs (Lesson 65).
- **[Claude] The defaults taken where the stage's wording leaves a choice**, each named here because
  nobody was asked:
  - The jobs, the models and the pipeline go through boto3's low-level client and a JSON pipeline
    definition rather than the SageMaker SDK. The lock's SDK is 3.21.0, whose training and pipeline
    classes are not the 2.x `Estimator` and `Pipeline` that AWS's recipe imports, and a request built
    field by field lets each negative change exactly one field (Lesson 20).
  - Step 2.2's image is XGBoost `3.0-5`, not the recipe's `1.7-1`, for the reason the next entry
    measures; the stage file's step 2.2 and its menu table carry the change.
  - `register.py log-model` logs the job's `model.tar.gz` into the job's MLflow run before it loads the
    booster, so verification iv has an object in the artifact store whatever the image.
    `register.py from-mlflow` calls `mlflow.register_model` on the job's `model.tar.gz` by its `s3://`
    URI, as the recipe does.
  - `ML-3` reads the account's 20 most recent training jobs whatever their name, where step 2.5 says
    every `ml-demo-` job, so the job a portal form creates (2.4) is judged too.
  - The knowledge base's documents are copied by `knowledge_base.py` from the space's clone, which prints
    the commit and each document's size for this log (7.4a).
- **[Claude] The model format, measured on the session's build host, not in the lab.** A booster that
  `xgboost` 1.7.6 saved as `xgboost-model`, the name the SageMaker XGBoost container uses, starts with
  the bytes `binf`, and `xgboost-cpu` 3.3.0 refused to load it:

  ```
  The binary format has been deprecated in 1.6 and removed in 3.1, use UBJ or JSON instead. You can
  port the binary model to UBJ and JSON by re-saving it with XGBoost 3.0.
  ```

  The same booster saved by `xgboost` 3.0.5 was UBJSON, and 3.3.0 loaded it with the warning
  ``Unknown file format: ``. Using UBJSON (`ubj`) as a guess.``. So with `1.7-1`, step 3.1's
  `mlflow.xgboost.log_model` cannot run in the house interpreter. The container's own source was not
  read: its repository is outside this session's GitHub scope, and AWS's XGBoost algorithm pages and the
  `us-west-2` registry-paths page did not load from it. `3.0-5` is in the same repository,
  `sagemaker-xgboost`, and the same `us-west-2` registry as `1.7-1` in the image table of `sagemaker-core`
  2.21.0, so `ML-3`'s image check reads both the same way.
- **[Claude] What else ran on that build host**, with fabricated account values:
  - `data.py` fetched the recipe's CSV through the host's proxy, not the lab's: 7,043 rows, 970,457
    bytes. `prepare.py` dropped 11 rows for a blank `TotalCharges` and split the rest 4,922 / 1,054 /
    1,056, byte-identical under `pandas` 2.3.3 and 3.0.6.
  - The recipe's hyperparameters, trained locally with `xgboost-cpu` 3.3.0 over that split, gave a
    validation AUC of 0.8181 at 200 rounds and depth 5 and 0.8415 at 50 rounds and depth 3, both above the
    pipeline's `AucThreshold` of 0.75. A job's AUC is the image's reading, not this one.
  - Every AWS call of the scripts but `register.py log-model`'s went through botocore's `Stubber`, which
    checks each request against the service model, with MLflow replaced by a stand-in; each variant of
    `train.py` differed from the admitted request in one top-level field.
- **[Claude] What the laptop owes next.** On the laptop, as the infrastructure user with
  `InfrastructureAccess` in `Sandbox` (`awsds-infra-sandbox-1`): `./aws/devenv.py`, whose `DE-5` `ML-9`
  reads, then `./aws/sandbox-ml.py`, with the session down or up; its interface-endpoint half of `ML-9`
  reads only after `make hub-up` and `make up ENV=sandbox`. In a space, the user's 0.3; in the portal, the
  user's 0.7.
