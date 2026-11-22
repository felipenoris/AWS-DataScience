"""What the tasks share: an S3 URI and the objects under it, the XCom an operator leaves, the
SHA-256 of an archive, the threshold a stage sets and the AUC computed by rank."""

from __future__ import annotations

import ast
import hashlib
import json
from urllib.parse import urlparse

# The tag every SageMaker resource a project creates carries, with the project's id.
PROJECT_TAG = "AmazonDataZoneProject"


def split_uri(uri: str) -> tuple[str, str]:
    """`s3://bucket/prefix/key` -> (`bucket`, `prefix/key`)."""
    parsed = urlparse(uri)
    if parsed.scheme != "s3" or not parsed.netloc:
        raise ValueError(f"not an s3:// URI: {uri}")
    return parsed.netloc, parsed.path.lstrip("/")


def folder(uri: str) -> str:
    """The URI with one trailing slash, the form a prefix is joined with a name in."""
    return uri.rstrip("/") + "/"


def read_bytes(s3, uri: str) -> bytes:
    bucket, key = split_uri(uri)
    return s3.get_object(Bucket=bucket, Key=key)["Body"].read()


def read_json(s3, uri: str) -> dict:
    return json.loads(read_bytes(s3, uri))


def write_bytes(s3, uri: str, body: bytes, content_type: str = "") -> dict:
    """The object written under the bucket's default encryption; the response, with its ETag."""
    bucket, key = split_uri(uri)
    extra = {"ContentType": content_type} if content_type else {}
    return s3.put_object(Bucket=bucket, Key=key, Body=body, **extra)


def write_json(s3, uri: str, document: dict) -> dict:
    body = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode()
    return write_bytes(s3, uri, body, "application/json")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decode_xcom(value: str | dict, task: str) -> dict:
    """An operator's XCom as the dict it pushed.

    The worker renders an XCom into a template as the JSON of its value (SUP-277), so the text is
    decoded until a dict appears; a dict, and the Python literal a template renders one as, are read
    too.
    """
    for _ in range(3):
        if not isinstance(value, str):
            break
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            try:
                value = ast.literal_eval(value)
            except (ValueError, SyntaxError) as exc:
                raise RuntimeError(f"the {task} task's XCom is neither JSON nor a literal") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"the {task} task's XCom is a {type(value).__name__}, not a mapping")
    return value


def threshold(min_auc: str | float) -> float:
    """MIN_AUC, the stage variable, as a number strictly between 0.5 and 1."""
    try:
        value = float(min_auc)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"MIN_AUC {min_auc!r} is not a number") from exc
    if not 0.5 < value < 1:
        raise RuntimeError(f"MIN_AUC {value} is not between 0.5 and 1")
    return value


def by_digest(image: str, what: str) -> str:
    """An image URI that names its digest; any other fails."""
    if "@sha256:" not in str(image):
        raise RuntimeError(f"the {what} {image!r} names no digest")
    return image


def auc_by_rank(scores: list[float], labels: list[int]) -> float:
    """The area under the ROC curve: the Mann-Whitney statistic over the scores' ranks, ties taking
    their mean rank."""
    if len(scores) != len(labels):
        raise RuntimeError(f"{len(scores)} score(s) for {len(labels)} label(s)")
    positives = sum(1 for label in labels if label == 1)
    negatives = len(labels) - positives
    if not positives or not negatives:
        raise RuntimeError("the AUC needs both labels among the rows")
    ordered = sorted(range(len(scores)), key=scores.__getitem__)
    ranks = [0.0] * len(scores)
    start = 0
    while start < len(ordered):
        end = start
        while end + 1 < len(ordered) and scores[ordered[end + 1]] == scores[ordered[start]]:
            end += 1
        for index in ordered[start : end + 1]:
            ranks[index] = (start + end) / 2 + 1
        start = end + 1
    rank_sum = sum(rank for rank, label in zip(ranks, labels, strict=True) if label == 1)
    return (rank_sum - positives * (positives + 1) / 2) / (positives * negatives)
