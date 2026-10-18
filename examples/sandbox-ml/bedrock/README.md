# The Generative AI objects of Stage 17

The records of [Stage 17](../../../docs/plan/stages/stage-17-sandbox-machine-learning.md)'s pass 7, which
the portal creates and this folder keeps once each has run. Nothing is here yet: pass 7 has not started.

| File, once it exists | What it records | Step |
|---|---|---|
| the prompt's, the guardrail's and the flow's exported definitions | each object as the portal saved it, every account-scoped value a placeholder under the names of [`../README.md`](../README.md), "The values" | 7.4 |
| the evaluation job's definition and its twenty-line dataset | the automatic evaluation over Claude Haiku 4.5 as the evaluator; the dataset is the copy written to the project's `shared/ml-demo/bedrock/` | 7.4 |
| the knowledge base's document list | what `../knowledge_base.py` printed: the commit, each runbook's key and size | 7.4a |
| the chat agent's exported snapshot | the app as shared, with its model id, its knowledge base and its guardrail | 7.4b |

The knowledge base reads its documents from the project bucket, never from this folder:
`../knowledge_base.py` copies the runbooks there, and the trail and `ML-8` read them in that one place.
