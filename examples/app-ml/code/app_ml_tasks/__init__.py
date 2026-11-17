"""app-ml's worker tasks, run by the MWAA Serverless worker with the boto3 it carries.

A Python task names its callable as `app_ml_tasks.<function>`, a module and its attribute, the shape
app-etl's tasks run in: `evaluate` and `publish` (app-ml-train, `app_ml_tasks.training`),
`register` (app-ml-register, `app_ml_tasks.registry`), `resolve` and `check` (app-ml-score,
`app_ml_tasks.scoring`). The Bash task `track` runs `python3 -m app_ml_tasks.track`, whose MLflow
client only code/app-ml-train.zip carries; nothing here imports it. What a task prints lands in the
workflow's log group, so the tasks print counts, names, identifiers, hashes and metrics, never a
value of the data.
"""

from .registry import register
from .scoring import check, resolve
from .training import evaluate, publish

__all__ = ["check", "evaluate", "publish", "register", "resolve"]
