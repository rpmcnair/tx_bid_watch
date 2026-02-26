from __future__ import annotations
import boto3

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import Settings, load_settings
from .soda_client import SodaClient


@dataclass(frozen=True)
class WatchResult:
    run_ts: str
    dataset_id: str
    domain: str
    lookback_hours: int
    pulled_rows: int
    output_path: str


def _run_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def write_raw_json_local(rows: list[dict[str, Any]], dataset_id: str, run_ts: str) -> Path:
    """
    Write raw rows to a timestamped JSON file under:
      data/raw/dataset=<dataset_id>/run=<run_ts>.json
    """
    out_dir = Path("data/raw") / f"dataset={dataset_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"run={run_ts}.json"
    out_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return out_path


def write_raw_json_s3(
    rows: list[dict[str, Any]],
    bucket: str,
    prefix: str,
    dataset_id: str,
    run_ts: str,
) -> str:
    """
    Write raw rows to S3 under:
      s3://<bucket>/<prefix>/dataset=<dataset_id>/run=<run_ts>.json
    Returns the S3 key.
    """
    key = f"{prefix}/dataset={dataset_id}/run={run_ts}.json"
    body = json.dumps(rows, indent=2).encode("utf-8")

    s3 = boto3.client("s3")
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ContentType="application/json",
    )
    return key


def run_watch(settings: Settings) -> WatchResult:
    client = SodaClient(domain=settings.soda_domain, dataset_id=settings.dataset_id)

    rows = client.fetch_updated_since(
        lookback_hours=settings.lookback_hours,
        page_limit=settings.page_limit,
        max_pages=settings.max_pages,
    )

    run_ts = _run_timestamp()

    if settings.raw_bucket:
        key = write_raw_json_s3(
            rows=rows,
            bucket=settings.raw_bucket,
            prefix=settings.raw_prefix,
            dataset_id=settings.dataset_id,
            run_ts=run_ts,
        )
        output_path = f"s3://{settings.raw_bucket}/{key}"
    else:
        out_path = write_raw_json_local(rows, settings.dataset_id, run_ts)
        output_path = str(out_path)

    return WatchResult(
        run_ts=run_ts,
        dataset_id=settings.dataset_id,
        domain=settings.soda_domain,
        lookback_hours=settings.lookback_hours,
        pulled_rows=len(rows),
        output_path=output_path,
    )


def main() -> None:
    """
    Convenience local entrypoint for running watch.py directly.
    """
    settings = load_settings()
    result = run_watch(settings)

    print("=== Texas Procurement Watch: Ingest Run ===")
    print(f"Domain:        {result.domain}")
    print(f"Dataset ID:    {result.dataset_id}")
    print(f"Lookback:      {result.lookback_hours} hours")
    print(f"Pulled rows:   {result.pulled_rows}")
    print(f"Saved to:      {result.output_path}")


if __name__ == "__main__":
    main()
