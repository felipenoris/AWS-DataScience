"""The doubles the tests share: botocore clients for a Stubber, offline and with stand-in
credentials, and an S3 double that serves the sample and keeps what a task writes."""

from __future__ import annotations

import io
from datetime import UTC, datetime

import boto3
import pytest

REGION = "us-west-2"
ACCOUNT = "000000000000"
NOW = datetime(2026, 11, 17, 12, 0, tzinfo=UTC)
BUCKET = "projects-bucket"
SHARED = f"s3://{BUCKET}/domain/project/shared/"


def client(service: str):
    """A client of the service, its credentials stand-ins so no profile of the machine is read."""
    session = boto3.session.Session(
        aws_access_key_id="stand-in",
        aws_secret_access_key="stand-in",
        region_name=REGION,
    )
    return session.client(service)


def operations(client_) -> list[str]:
    """The names of the operations the client is asked for, in order. The event precedes the one a
    Stubber answers on, and every handler of it runs."""
    calls: list[str] = []

    def record(model, **_):
        calls.append(model.name)

    client_.meta.events.register("before-parameter-build.*.*", record)
    return calls


class FakeS3:
    """get_object and put_object over a dict of (bucket, key) -> bytes."""

    def __init__(self, objects: dict | None = None):
        self.objects = dict(objects or {})
        self.content_types: dict = {}

    def get_object(self, Bucket: str, Key: str) -> dict:
        return {"Body": io.BytesIO(self.objects[(Bucket, Key)])}

    def put_object(self, Bucket: str, Key: str, Body: bytes, ContentType: str) -> dict:
        self.objects[(Bucket, Key)] = Body
        self.content_types[(Bucket, Key)] = ContentType
        return {}

    def text(self, key: str) -> str:
        return self.objects[(BUCKET, key)].decode("utf-8")


@pytest.fixture
def boto3_clients(monkeypatch):
    """boto3.client answered from a dict the test fills, by service name."""
    clients: dict = {}
    monkeypatch.setattr(boto3, "client", lambda service, **_: clients[service])
    return clients
