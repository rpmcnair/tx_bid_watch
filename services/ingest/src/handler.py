from __future__ import annotations

import json
import os
from dataclasses import asdict

import boto3

from .config import load_settings
from .watch import run_watch


def lambda_handler(event, context):
    """
    AWS Lambda entrypoint.

    Uses env vars via load_settings(), runs one ingest, writes to S3 if RAW_BUCKET is set.
    If SNS_TOPIC_ARN is set, publishes a run summary to SNS.
    If CURATE_LAMBDA_NAME is set, asynchronously invokes the curate Lambda
    with dataset/run_date/run_ts for incremental curated loading.
    Returns a JSON-serializable dict for logs/observability.
    """
    settings = load_settings()
    result = run_watch(settings)

    payload = asdict(result)
    print(payload)

    topic_arn = os.getenv("SNS_TOPIC_ARN", "").strip()
    if topic_arn:
        sns = boto3.client("sns")
        message = (
            "TX Bid Watch ingest run completed\n"
            f"Run: {payload['run_ts']}\n"
            f"Run date: {payload['run_date']}\n"
            f"Dataset: {payload['dataset_id']}\n"
            f"Rows: {payload['pulled_rows']}\n"
            f"Output: {payload['output_path']}\n"
        )

        sns.publish(
            TopicArn=topic_arn,
            Subject="TX Bid Watch: ingest complete",
            Message=message,
        )

    curate_lambda_name = os.getenv("CURATE_LAMBDA_NAME", "").strip()
    if curate_lambda_name:
        lambda_client = boto3.client("lambda")
        curate_payload = {
            "dataset": payload["dataset_id"],
            "run_date": payload["run_date"],
            "run_ts": payload["run_ts"],
        }

        lambda_client.invoke(
            FunctionName=curate_lambda_name,
            InvocationType="Event",
            Payload=json.dumps(curate_payload).encode("utf-8"),
        )

        print({"curate_invoked": True, "curate_payload": curate_payload})

    return payload