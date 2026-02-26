from __future__ import annotations

import json
from src import watch


def test_write_raw_json_s3_puts_object(monkeypatch):
    captured = {}

    class DummyS3:
        def put_object(self, Bucket, Key, Body, ContentType):
            captured["Bucket"] = Bucket
            captured["Key"] = Key
            captured["Body"] = Body
            captured["ContentType"] = ContentType

    def fake_boto3_client(name: str):
        assert name == "s3"
        return DummyS3()

    monkeypatch.setattr(watch.boto3, "client", fake_boto3_client)

    rows = [{"a": 1}, {"b": 2}]
    key = watch.write_raw_json_s3(
        rows=rows,
        bucket="my-bucket",
        prefix="raw",
        dataset_id="qh8x-rm8r",
        run_ts="20260224T123456Z",
    )

    assert key == "raw/dataset=qh8x-rm8r/run=20260224T123456Z.json"
    assert captured["Bucket"] == "my-bucket"
    assert captured["Key"] == key
    assert captured["ContentType"] == "application/json"

    decoded = json.loads(captured["Body"].decode("utf-8"))
    assert decoded == rows