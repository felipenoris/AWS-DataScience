"""app-genai's worker tasks, one callable per task of its workflows.

- `ensure_guardrail`, the `guardrail` task of app-genai-triage: the application's guardrail kept as
  `guardrail/definition.json` defines it, its published version returned (`guardrail`).
- `triage_messages`, the `triage` task: each message of the sample sent to the model under that
  version, the answers written (`triage`).
- `check_answers`, the `check` task: the answers held to the sample, the prompt's labels and the
  guardrail's trace, the report written (`check`).
- `probe_unguarded`, the `unguarded` task of app-genai-probe: one request with no guardrail, its
  outcome held to EXPECT_UNGUARDED (`probe`).

They run on the MWAA Serverless worker with the boto3 the worker carries, 1.43.1. The pipeline zips
this package with `prompts/triage.md` and `guardrail/definition.json` beside it into
`code/app-genai.zip`, the `code` of both workflows; the worker extracts the archive to a folder on
`sys.path`, so a workflow names a callable as `app_genai_tasks.<function>` and a task reads a file
beside the package. What the tasks print lands in the workflow's log group, so they print counts,
names, identifiers and outcomes, never a message or an answer.
"""

from .check import check_answers
from .guardrail import ensure_guardrail
from .probe import probe_unguarded
from .triage import triage_messages

__all__ = ["check_answers", "ensure_guardrail", "probe_unguarded", "triage_messages"]
