from __future__ import annotations

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
            f"Dataset: {payload['dataset_id']}\n"
            f"Rows: {payload['pulled_rows']}\n"
            f"Output: {payload['output_path']}\n"
        )

        sns.publish(
            TopicArn=topic_arn,
            Subject="TX Bid Watch: ingest complete",
            Message=message,
        )

    return payload