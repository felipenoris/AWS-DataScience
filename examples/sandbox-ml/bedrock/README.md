# The Generative AI objects of Stage 17

The records of [Stage 17](../../../docs/plan/stages/stage-17-sandbox-machine-learning.md)'s pass 7, which
the portal creates and this folder keeps once each has run. Pass 7 has not started; the one file written
before it is 7.4's dataset.

| File, once it exists | What it records | Step |
|---|---|---|
| the prompt's, the guardrail's and the flow's exported definitions | each object as the portal saved it, every account-scoped value a placeholder under the names of [`../README.md`](../README.md), "The values" | 7.4 |
| `evaluation-dataset.jsonl`, written before the run | twenty prompts of the task *Question and answer*, each line a `prompt`, a `referenceResponse` and a `category`, the keys of AWS's custom prompt dataset; `../evaluation_dataset.py` copies it to the project's `shared/ml-demo/bedrock/` | 7.4 |
| the evaluation job's definition | the automatic evaluation of Claude Haiku 4.5 over that dataset; the IDE offers no judge model | 7.4 |
| the knowledge base's document list | what `../knowledge_base.py` printed: the commit, each runbook's key and size | 7.4a |
| the chat agent's exported snapshot | the app as shared, with its model id, its knowledge base and its guardrail | 7.4b |

The knowledge base reads its documents from the project bucket, never from this folder:
`../knowledge_base.py` copies the runbooks there, and the trail and `ML-8` read them in that one place.
