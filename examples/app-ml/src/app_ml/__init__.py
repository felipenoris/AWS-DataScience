"""app-ml: a churn table becomes XGBoost's training and scoring sets.

The package is the code a SageMaker processing job runs from the application image, in two modes:
`python -m app_ml.prepare train` writes the training and validation sets from the churn table, and
`python -m app_ml.prepare score` writes the batch set and its labels from the labelled holdout.
"""

__version__ = "0.1.0"
