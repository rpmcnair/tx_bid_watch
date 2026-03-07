from __future__ import annotations

from dataclasses import asdict

from .config import load_settings
from .watch import run_watch


def lambda_handler(event, context):
    """
    AWS Lambda entrypoint.

    Uses env vars via load_settings(), runs one ingest, writes to S3 if RAW_BUCKET is set.
    Returns a JSON-serializable dict for logs/observability.
    """
    settings = load_settings()
    result = run_watch(settings)
    return asdict(result)