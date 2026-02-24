from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
import os


def fetch_updated_since(
    domain: str,
    dataset_id: str,
    lookback_hours: int,
    page_limit: int,
    max_pages: int,
) -> list[dict]:
    """Fetch rows updated in the last `lookback_hours` using Socrata SODA."""
    since = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    since_str = since.replace(microsecond=0).isoformat().replace("+00:00", "Z")

    url = f"https://{domain}/resource/{dataset_id}.json"
    all_rows: list[dict] = []
    offset = 0

    for _ in range(max_pages):
        params = {
            "$limit": page_limit,
            "$offset": offset,
            "$where": f":updated_at >= '{since_str}'",
            "$order": ":updated_at ASC", 
        }
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        rows = resp.json()
        if not isinstance(rows, list):
            raise ValueError(f"Unexpected response type: {type(rows)}")

        all_rows.extend(rows)

        if len(rows) < page_limit:
            break
        offset += page_limit

    return all_rows


def main() -> None:
    load_dotenv()

    domain = os.getenv("SODA_DOMAIN", "data.texas.gov").strip()
    dataset_id = os.getenv("DATASET_ID", "qh8x-rm8r").strip()
    lookback_hours = int(os.getenv("LOOKBACK_HOURS", "24"))
    page_limit = int(os.getenv("PAGE_LIMIT", "1000"))
    max_pages = int(os.getenv("MAX_PAGES", "2"))

    rows = fetch_updated_since(
        domain=domain,
        dataset_id=dataset_id,
        lookback_hours=lookback_hours,
        page_limit=page_limit,
        max_pages=max_pages,
    )

    run_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path("data/raw") / f"dataset={dataset_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"run={run_ts}.json"
    out_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    print("=== Texas Procurement Watch: Local Ingest ===")
    print(f"Domain:        {domain}")
    print(f"Dataset ID:    {dataset_id}")
    print(f"Lookback:      {lookback_hours} hours")
    print(f"Pulled rows:   {len(rows)}")
    print(f"Saved to:      {out_path}")

    if rows:
        print("\nSample keys from first row:")
        print(sorted(rows[0].keys())[:25])


if __name__ == "__main__":
    main()
